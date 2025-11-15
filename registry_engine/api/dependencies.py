"""FastAPI dependencies."""

from typing import Generator

from sqlalchemy.orm import Session

from registry_engine.database import get_db, SubAgentDB, PromptDB, InterfaceDB


def get_session() -> Generator[Session, None, None]:
    """Get database session dependency.

    Yields:
        Database session
    """
    db = get_db()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def get_subagent_db(session: Session = None) -> SubAgentDB:
    """Get SubAgent database operations.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        SubAgentDB instance
    """
    return SubAgentDB(session)


def get_prompt_db(session: Session = None) -> PromptDB:
    """Get Prompt database operations.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        PromptDB instance
    """
    return PromptDB(session)


def get_interface_db(session: Session = None) -> InterfaceDB:
    """Get Interface database operations.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        InterfaceDB instance
    """
    return InterfaceDB(session)
