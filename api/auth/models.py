from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import Integer, String, ForeignKey, Column
from sqlalchemy.orm import relationship

from api.config.models import Base


class GroupUserAssociation(Base):
    __tablename__ = 'group_user_association'

    group_id = Column(Integer, ForeignKey('group.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)


class User(SQLAlchemyBaseUserTable[int], Base):
    id: int = Column(Integer, primary_key=True)
    email: str = Column(
            String(length=320), unique=True, index=True, nullable=False,
        )
    username: str = Column(
        String(length=320), unique=True, index=True,  nullable=True,
    )

    role: int = Column(
        ForeignKey("roles.id"), nullable=False, default=1
    )
    groups = relationship("Group", secondary='group_user_association', back_populates="users")
