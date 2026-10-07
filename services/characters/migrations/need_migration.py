from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    """Upgrade schema."""
    # Создаем последовательность
    op.execute("CREATE SEQUENCE slot_number_seq START 1")
    
    # Меняем столбец number на использование последовательности
    op.alter_column('slots', 'number', 
                   server_default=sa.text("nextval('slot_number_seq'::regclass)"))
    
    # Устанавливаем текущее значение последовательности на максимальное существующее значение + 1
    op.execute("SELECT setval('slot_number_seq', (SELECT COALESCE(MAX(number), 0) + 1 FROM slots))")


def downgrade() -> None:
    """Downgrade schema."""
    # Убираем использование последовательности
    op.alter_column('slots', 'number', server_default=None)
    
    # Удаляем последовательность
    op.execute("DROP SEQUENCE slot_number_seq")