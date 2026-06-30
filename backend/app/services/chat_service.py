"""Chat Service — orchestrates conversation flow with ProfileMiningAgent."""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from app.models.conversation import Conversation, Message
from app.models.profile import Profile, ProfileVersion
from app.models.user import User
from app.agents.profile_mining import ProfileMiningAgent


class ChatService:
    """Manages conversation sessions and message processing."""

    def __init__(self, agent: ProfileMiningAgent, db_factory):
        self.agent = agent
        self.db_factory = db_factory

    def create_session(self, user_id: int | None = None) -> dict:
        """Create a new conversation session."""
        db = self.db_factory()
        try:
            conv = Conversation(
                user_id=user_id or 1,  # Default user for demo
                state={
                    "phase": "greeting",
                    "collected_fields": [],
                    "questions_asked": 0,
                },
                status="active",
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

            greeting = self.agent.get_greeting()

            # Save greeting as system message
            sys_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=greeting,
                extra_data={"phase": "greeting"},
            )
            db.add(sys_msg)
            db.commit()

            return {
                "session_id": conv.id,
                "greeting_message": greeting,
                "phase": "greeting",
                "user_id": conv.user_id,
            }
        finally:
            db.close()

    async def process_message(self, session_id: int, content: str) -> dict:
        """Process a user message: generate reply + extract profile data."""
        db = self.db_factory()
        try:
            conv = db.query(Conversation).filter(Conversation.id == session_id).first()
            if not conv:
                return {"error": "Session not found"}

            # Save user message
            user_msg = Message(
                conversation_id=session_id,
                role="user",
                content=content,
            )
            db.add(user_msg)
            db.commit()

            # Build conversation context from recent messages
            recent_msgs = (
                db.query(Message)
                .filter(Message.conversation_id == session_id)
                .order_by(Message.created_at.desc())
                .limit(6)
                .all()
            )
            context = "\n".join(
                f"{'用户' if m.role == 'user' else '助手'}: {m.content}"
                for m in reversed(recent_msgs)
            )

            # Get current profile
            profile = db.query(Profile).filter(Profile.user_id == conv.user_id).first()
            profile_json = json.dumps(profile.to_dict() if profile else {}, ensure_ascii=False)

            # Collect info already gathered
            collected_info = conv.state.get("collected_fields", [])
            if profile:
                if profile.interests:
                    collected_info.append(
                        f"兴趣: {[i.get('sub_category', '') for i in profile.interests]}"
                    )
                if profile.personality:
                    collected_info.append(
                        f"性格: {profile.personality}"
                    )
                if profile.social_need:
                    collected_info.append(
                        f"社交需求: {profile.social_need}"
                    )

            # Call ProfileMiningAgent
            from app.agents.base import AgentRequest
            response = await self.agent.process(AgentRequest(
                caller="chat_service",
                payload={
                    "action": "chat",
                    "user_message": content,
                    "current_phase": conv.state.get("phase", "greeting"),
                    "collected_info": {"fields": collected_info},
                    "conversation_context": context,
                    "current_profile_json": profile_json,
                },
            ))

            if response.status == "error":
                logger.error(f"Agent error: {response.error}")
                # Return a fallback reply
                assistant_msg = Message(
                    conversation_id=session_id,
                    role="assistant",
                    content="抱歉，我暂时无法处理。可以再说说你的想法吗？",
                    extra_data={"phase": conv.state.get("phase"), "error": response.error},
                )
                db.add(assistant_msg)
                db.commit()
                return {
                    "message_id": assistant_msg.id,
                    "role": "assistant",
                    "content": assistant_msg.content,
                    "phase": conv.state.get("phase"),
                    "extracted_tags": [],
                }

            payload = response.payload
            reply = payload.get("reply", "")
            new_phase = payload.get("new_phase", conv.state.get("phase"))
            extractions = payload.get("extractions", [])

            # Update conversation state
            conv.state = {
                "phase": new_phase,
                "collected_fields": collected_info,
                "questions_asked": conv.state.get("questions_asked", 0) + 1,
            }
            conv.updated_at = datetime.utcnow()

            # Save assistant message
            assistant_msg = Message(
                conversation_id=session_id,
                role="assistant",
                content=reply,
                extra_data={
                    "phase": new_phase,
                    "extracted_tags": extractions,
                    "tokens_used": response.tokens_used,
                },
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)

            # Update profile with extractions
            profile_updates = None
            if extractions and profile:
                profile_updates = self._apply_extractions(db, profile, extractions)

            return {
                "message_id": assistant_msg.id,
                "role": "assistant",
                "content": reply,
                "phase": new_phase,
                "extracted_tags": extractions,
                "profile_updates": profile_updates,
                "tokens_used": response.tokens_used,
                "latency_ms": response.latency_ms,
            }
        finally:
            db.close()

    def _apply_extractions(
        self, db: Session, profile: Profile, extractions: list[dict]
    ) -> dict | None:
        """Apply extracted tags to profile, creating new version if changes detected."""
        changed = False
        existing_interest_keys = {
            (i.get("category", ""), i.get("sub_category", ""))
            for i in (profile.interests or [])
        }

        for ext in extractions:
            if ext.get("type") == "interest":
                key = (ext.get("category", ""), ext.get("sub_category", ""))
                if key not in existing_interest_keys:
                    profile.interests.append({
                        "category": ext.get("category", ""),
                        "sub_category": ext.get("sub_category", ""),
                        "weight": ext.get("weight", 0.5),
                        "confidence": ext.get("confidence", 0.5),
                        "source": "dialogue",
                        "source_quote": ext.get("source_quote", ""),
                    })
                    existing_interest_keys.add(key)
                    changed = True

            elif ext.get("type") == "personality":
                trait = ext.get("trait", "")
                value = ext.get("value", 0.5)
                if trait in ("openness", "extraversion", "conscientiousness"):
                    old_val = profile.personality.get(trait, 0.5)
                    # Weighted update: new value has weight proportional to confidence
                    conf = ext.get("confidence", 0.5)
                    new_val = old_val * (1 - conf * 0.5) + value * conf * 0.5
                    profile.personality[trait] = round(new_val, 2)
                    changed = True

            elif ext.get("type") == "social_need":
                field = ext.get("field", "")
                value = ext.get("value", "")
                if field and value:
                    profile.social_need[field] = value
                    changed = True

        if changed:
            # Save version snapshot
            snapshot = profile.create_snapshot()
            version = ProfileVersion(
                profile_id=profile.id,
                version=profile.version + 1,
                snapshot=snapshot,
                change_reason=f"对话提取: {len(extractions)} 个新标签",
            )
            db.add(version)
            profile.version += 1
            db.commit()
            db.refresh(profile)

            return {
                "added_interests": [
                    e for e in extractions if e.get("type") == "interest"
                ],
                "updated_personality": profile.personality,
                "updated_social_need": profile.social_need,
                "new_version": profile.version,
            }

        return None

    def get_session(self, session_id: int) -> dict | None:
        """Get full conversation with messages."""
        db = self.db_factory()
        try:
            conv = db.query(Conversation).filter(Conversation.id == session_id).first()
            if not conv:
                return None

            return {
                "id": conv.id,
                "user_id": conv.user_id,
                "state": conv.state,
                "status": conv.status,
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "metadata": m.extra_data,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in (conv.messages or [])
                ],
                "started_at": conv.started_at.isoformat() if conv.started_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            }
        finally:
            db.close()

    def list_sessions(self, user_id: int, page: int = 1, limit: int = 20) -> dict:
        """List user's conversation sessions."""
        db = self.db_factory()
        try:
            query = db.query(Conversation).filter(Conversation.user_id == user_id)
            total = query.count()
            convs = (
                query.order_by(Conversation.updated_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )
            return {
                "items": [
                    {
                        "id": c.id,
                        "status": c.status,
                        "message_count": len(c.messages) if c.messages else 0,
                        "phase": c.state.get("phase") if c.state else None,
                        "started_at": c.started_at.isoformat() if c.started_at else None,
                        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                    }
                    for c in convs
                ],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if limit > 0 else 0,
            }
        finally:
            db.close()
