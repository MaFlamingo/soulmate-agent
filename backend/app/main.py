"""SoulMate-Agent — FastAPI application entry point.

Wires up the three core agents, services, and API routes.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure backend/ is on sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.core.database import init_db, SessionLocal
from app.core.llm_adapter import (
    LLMAdapterFactory,
    get_llm_config_from_settings,
)
from app.core.embedding import init_embedding_client
from app.core.vector_store import get_collection_stats

# Agents
from app.agents.profile_mining import ProfileMiningAgent
from app.agents.matching_decision import MatchingDecisionAgent
from app.agents.facilitation import FacilitationAgent

# Services
from app.services.chat_service import ChatService
from app.services.profile_service import ProfileService
from app.services.matching_service import MatchingService
from app.services.admin_service import AdminService

# API routes
from app.api.chat import router as chat_router
from app.api.profile import router as profile_router
from app.api.match import router as match_router
from app.api.admin import router as admin_router

# Middleware
from app.middleware.error_handler import global_exception_handler
from app.middleware.audit import AuditMiddleware

# Rule engine init
from app.engine.rule_engine import get_rule_engine


# ── Application State ────────────────────────────────────────────


class AppState:
    """Holds shared service instances accessible via request.app.state."""
    chat_service: ChatService
    profile_service: ProfileService
    matching_service: MatchingService
    admin_service: AdminService
    llm_adapter = None
    embedding_client = None


# ── Lifespan ──────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("=" * 60)
    logger.info("SoulMate-Agent starting up...")
    logger.info("=" * 60)

    # 1. Initialize database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database tables created/verified")

    # 2. Initialize LLM adapter
    logger.info(f"Initializing LLM: provider={settings.llm_provider}, model={settings.llm_model}")
    llm_config = get_llm_config_from_settings()
    llm = LLMAdapterFactory.create(llm_config)
    logger.info("LLM adapter ready")

    # 3. Initialize embedding client
    init_embedding_client(llm)
    from app.core.embedding import get_embedding_client
    emb_client = get_embedding_client()
    logger.info("Embedding client ready")

    # 4. Initialize agents
    profile_mining_agent = ProfileMiningAgent(llm)
    matching_decision_agent = MatchingDecisionAgent(llm, emb_client, SessionLocal)
    facilitation_agent = FacilitationAgent(llm)
    logger.info("All 3 agents initialized")

    # 5. Initialize services
    chat_service = ChatService(profile_mining_agent, SessionLocal)
    profile_service = ProfileService(SessionLocal)
    matching_service = MatchingService(matching_decision_agent, facilitation_agent, SessionLocal)
    admin_service = AdminService(SessionLocal)
    logger.info("All services initialized")

    # 6. Load matching rules into rule engine
    db = SessionLocal()
    try:
        from app.models.matching_rule import MatchingRule
        rules = db.query(MatchingRule).all()
        # Seed default rules if empty
        if not rules:
            _seed_default_rules(db)
            rules = db.query(MatchingRule).all()
        get_rule_engine().load_rules(rules)
        logger.info(f"Rule engine loaded with {len(rules)} rules")
    finally:
        db.close()

    # 7. Seed demo users if none exist
    db = SessionLocal()
    try:
        from app.models.user import User
        user_count = db.query(User).count()
        if user_count == 0:
            _seed_demo_users(db)
            logger.info("Demo users seeded")
        else:
            logger.info(f"Database has {user_count} existing users")
    finally:
        db.close()

    # 8. Vector store check
    vs_stats = get_collection_stats()
    logger.info(f"Vector store: {vs_stats}")

    # 9. Attach to app state
    app.state.chat_service = chat_service
    app.state.profile_service = profile_service
    app.state.matching_service = matching_service
    app.state.admin_service = admin_service
    app.state.llm_adapter = llm
    app.state.embedding_client = emb_client

    logger.info("SoulMate-Agent is ready! 🚀")
    logger.info(f"API docs: http://{settings.host}:{settings.port}/docs")

    yield  # Application runs here

    # Shutdown
    logger.info("SoulMate-Agent shutting down...")


# ── App Creation ──────────────────────────────────────────────────


app = FastAPI(
    title="SoulMate-Agent",
    description="基于多智能体的对话式社交匹配系统 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit middleware
app.add_middleware(AuditMiddleware)

# Global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Register API routers
app.include_router(chat_router)
app.include_router(profile_router)
app.include_router(match_router)
app.include_router(admin_router)


# ── Health Check ──────────────────────────────────────────────────


@app.get("/")
async def root():
    return {
        "name": "SoulMate-Agent",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    vs_stats = get_collection_stats()
    return {
        "status": "healthy",
        "vector_store": vs_stats,
    }


# ── Seed Data ─────────────────────────────────────────────────────


def _seed_default_rules(db):
    """Seed default matching rules."""
    from app.models.matching_rule import MatchingRule

    defaults = [
        MatchingRule(
            name="same_city_filter",
            rule_type="hard_filter",
            config={"dimension": "city", "operator": "same_city"},
            priority=1,
            enabled=True,
            description="只匹配同城用户",
        ),
        MatchingRule(
            name="no_smoking_filter",
            rule_type="hard_filter",
            config={"dimension": "no_smoking", "operator": "eq", "value": True},
            priority=2,
            enabled=False,
            description="排除吸烟用户",
        ),
        MatchingRule(
            name="interest_weight",
            rule_type="weight",
            config={"dimension": "interest", "weight": 0.50},
            priority=10,
            enabled=True,
            description="兴趣相似度权重50%",
        ),
        MatchingRule(
            name="personality_weight",
            rule_type="weight",
            config={"dimension": "personality", "weight": 0.30},
            priority=11,
            enabled=True,
            description="性格契合度权重30%",
        ),
        MatchingRule(
            name="social_weight",
            rule_type="weight",
            config={"dimension": "social", "weight": 0.20},
            priority=12,
            enabled=True,
            description="社交需求匹配权重20%",
        ),
    ]
    for rule in defaults:
        db.add(rule)
    db.commit()
    logger.info(f"Seeded {len(defaults)} default matching rules")


def _seed_demo_users(db):
    """Seed demo users with diverse profiles for testing."""
    from app.models.user import User
    from app.models.profile import Profile
    from app.core.vector_store import upsert_profile_embedding

    demo_users = [
        {
            "username": "alice_wang",
            "email": "alice@example.com",
            "password_hash": "demo_hash",
            "display_name": "Alice",
            "city": "上海",
            "age_range": "25-30",
            "gender": "female",
            "interests": [
                {"category": "outdoor", "sub_category": "hiking", "weight": 0.9, "confidence": 0.95, "source": "seed"},
                {"category": "food", "sub_category": "coffee", "weight": 0.8, "confidence": 0.9, "source": "seed"},
                {"category": "travel", "sub_category": "backpacking", "weight": 0.7, "confidence": 0.85, "source": "seed"},
            ],
            "personality": {"openness": 0.8, "extraversion": 0.65, "conscientiousness": 0.7},
            "social_need": {"buddy_type": "hobby_partner", "schedule": "weekends"},
        },
        {
            "username": "bob_li",
            "email": "bob@example.com",
            "password_hash": "demo_hash",
            "display_name": "Bob",
            "city": "上海",
            "age_range": "25-30",
            "gender": "male",
            "interests": [
                {"category": "outdoor", "sub_category": "hiking", "weight": 0.85, "confidence": 0.9, "source": "seed"},
                {"category": "sports", "sub_category": "badminton", "weight": 0.8, "confidence": 0.9, "source": "seed"},
                {"category": "tech", "sub_category": "AI", "weight": 0.6, "confidence": 0.8, "source": "seed"},
            ],
            "personality": {"openness": 0.6, "extraversion": 0.4, "conscientiousness": 0.8},
            "social_need": {"buddy_type": "workout_partner", "schedule": "weekends"},
        },
        {
            "username": "carol_chen",
            "email": "carol@example.com",
            "password_hash": "demo_hash",
            "display_name": "Carol",
            "city": "上海",
            "age_range": "25-30",
            "gender": "female",
            "interests": [
                {"category": "outdoor", "sub_category": "camping", "weight": 0.9, "confidence": 0.95, "source": "seed"},
                {"category": "food", "sub_category": "coffee", "weight": 0.7, "confidence": 0.85, "source": "seed"},
                {"category": "reading", "sub_category": "scifi", "weight": 0.6, "confidence": 0.8, "source": "seed"},
            ],
            "personality": {"openness": 0.75, "extraversion": 0.3, "conscientiousness": 0.6},
            "social_need": {"buddy_type": "hobby_partner", "schedule": "flexible"},
        },
        {
            "username": "david_zhang",
            "email": "david@example.com",
            "password_hash": "demo_hash",
            "display_name": "David",
            "city": "北京",
            "age_range": "31-40",
            "gender": "male",
            "interests": [
                {"category": "sports", "sub_category": "basketball", "weight": 0.9, "confidence": 0.95, "source": "seed"},
                {"category": "tech", "sub_category": "startup", "weight": 0.8, "confidence": 0.9, "source": "seed"},
                {"category": "travel", "sub_category": "roadtrip", "weight": 0.7, "confidence": 0.85, "source": "seed"},
            ],
            "personality": {"openness": 0.7, "extraversion": 0.8, "conscientiousness": 0.5},
            "social_need": {"buddy_type": "workout_partner", "schedule": "weekday_evenings"},
        },
        {
            "username": "eve_liu",
            "email": "eve@example.com",
            "password_hash": "demo_hash",
            "display_name": "Eve",
            "city": "上海",
            "age_range": "18-24",
            "gender": "female",
            "interests": [
                {"category": "outdoor", "sub_category": "hiking", "weight": 0.8, "confidence": 0.9, "source": "seed"},
                {"category": "music", "sub_category": "indie", "weight": 0.7, "confidence": 0.85, "source": "seed"},
                {"category": "food", "sub_category": "streetfood", "weight": 0.85, "confidence": 0.9, "source": "seed"},
            ],
            "personality": {"openness": 0.85, "extraversion": 0.7, "conscientiousness": 0.4},
            "social_need": {"buddy_type": "foodie_buddy", "schedule": "weekends"},
        },
        {
            "username": "frank_wu",
            "email": "frank@example.com",
            "password_hash": "demo_hash",
            "display_name": "Frank",
            "city": "上海",
            "age_range": "25-30",
            "gender": "male",
            "interests": [
                {"category": "fitness", "sub_category": "gym", "weight": 0.9, "confidence": 0.95, "source": "seed"},
                {"category": "outdoor", "sub_category": "hiking", "weight": 0.6, "confidence": 0.8, "source": "seed"},
                {"category": "gaming", "sub_category": "boardgames", "weight": 0.7, "confidence": 0.85, "source": "seed"},
            ],
            "personality": {"openness": 0.5, "extraversion": 0.55, "conscientiousness": 0.9},
            "social_need": {"buddy_type": "workout_partner", "schedule": "weekday_evenings"},
        },
        {
            "username": "grace_zhao",
            "email": "grace@example.com",
            "password_hash": "demo_hash",
            "display_name": "Grace",
            "city": "杭州",
            "age_range": "25-30",
            "gender": "female",
            "interests": [
                {"category": "travel", "sub_category": "backpacking", "weight": 0.9, "confidence": 0.95, "source": "seed"},
                {"category": "art", "sub_category": "photography", "weight": 0.8, "confidence": 0.9, "source": "seed"},
                {"category": "reading", "sub_category": "literature", "weight": 0.7, "confidence": 0.85, "source": "seed"},
            ],
            "personality": {"openness": 0.9, "extraversion": 0.5, "conscientiousness": 0.6},
            "social_need": {"buddy_type": "travel_mate", "schedule": "flexible"},
        },
        {
            "username": "henry_xu",
            "email": "henry@example.com",
            "password_hash": "demo_hash",
            "display_name": "Henry",
            "city": "上海",
            "age_range": "31-40",
            "gender": "male",
            "interests": [
                {"category": "food", "sub_category": "coffee", "weight": 0.9, "confidence": 0.95, "source": "seed"},
                {"category": "reading", "sub_category": "business", "weight": 0.7, "confidence": 0.85, "source": "seed"},
                {"category": "tech", "sub_category": "AI", "weight": 0.85, "confidence": 0.9, "source": "seed"},
            ],
            "personality": {"openness": 0.65, "extraversion": 0.6, "conscientiousness": 0.75},
            "social_need": {"buddy_type": "study_buddy", "schedule": "weekday_evenings"},
        },
    ]

    # Use hashlib for demo accounts (passlib/bcrypt has compatibility issues on some platforms)
    import hashlib
    demo_hash = hashlib.sha256("demo123".encode()).hexdigest()

    for data in demo_users:
        user = User(
            username=data["username"],
            email=data["email"],
            password_hash=demo_hash,
            display_name=data["display_name"],
            city=data["city"],
            age_range=data["age_range"],
            gender=data["gender"],
        )
        db.add(user)
        db.flush()  # Get user.id

        profile = Profile(
            user_id=user.id,
            interests=data["interests"],
            personality=data["personality"],
            social_need=data["social_need"],
            static_attrs={"city": data["city"], "age_range": data["age_range"], "gender": data["gender"]},
            preferences={},
        )
        db.add(profile)
        db.flush()

        # Generate embedding for this user
        try:
            from app.core.embedding import get_embedding_client
            import asyncio
            emb = get_embedding_client()
            text = emb.profile_to_text(profile.to_dict())

            # Run embedding sync for seeding (ok since we're in startup)
            import time
            embedding = None
            try:
                # Try to use the LLM to embed
                embedding = None  # Will be lazy-generated on first match request
            except Exception:
                pass

            # Store a placeholder — real embedding done on first match
            if embedding:
                upsert_profile_embedding(user.id, embedding, {"city": data["city"]})
        except Exception as e:
            logger.warning(f"Could not pre-generate embedding for {user.username}: {e}")

    db.commit()
    logger.info(f"Seeded {len(demo_users)} demo users with profiles")


# ── Run ────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )
