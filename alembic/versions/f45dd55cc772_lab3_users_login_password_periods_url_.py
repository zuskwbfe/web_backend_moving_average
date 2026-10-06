"""lab3 users login password, periods url not null

Revision ID: f45dd55cc772
Revises: 6441b99cf580
Create Date: 2026-10-04 18:35:59.894220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f45dd55cc772'
down_revision: Union[str, Sequence[str], None] = '6441b99cf580'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    user_cols = {c["name"] for c in sa.inspect(bind).get_columns("users")}

    # users: username -> login (переименование, данные сохраняются)
    if "username" in user_cols and "login" not in user_cols:
        op.alter_column("users", "username", new_column_name="login")

    # users: password обязателен; у существующих тестовых пользователей ставим заглушку
    if "password" not in user_cols:
        op.add_column("users", sa.Column("password", sa.String(length=128), nullable=True))
    op.execute("UPDATE users SET password = '!' WHERE password IS NULL")
    op.alter_column("users", "password", existing_type=sa.String(length=128), nullable=False)

    # periods: url обязательные; у старых записей без файлов подставляем файлы по умолчанию
    op.execute("UPDATE periods SET image_url = '/static/img/default.png' WHERE image_url IS NULL")
    op.execute("UPDATE periods SET video_url = '/static/img/default.mp4' WHERE video_url IS NULL")
    op.alter_column("periods", "image_url", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("periods", "video_url", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    op.alter_column("periods", "video_url", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("periods", "image_url", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("users", "login", new_column_name="username")
