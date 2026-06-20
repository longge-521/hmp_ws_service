from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.message.entities import SiteMessage
from app.domain.message.repositories import MessageRepository
from app.infrastructure.database.models import SiteMessageORM, UploadedFileORM
from app.domain.upload.entities import UploadedFile
from app.domain.upload.repositories import UploadedFileRepository

class SQLMessageRepository(MessageRepository):
    """MessageRepository 契约的 MySQL 具体实现"""

    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, orm: SiteMessageORM) -> SiteMessage:
        if not orm:
            return None
        return SiteMessage(
            id=orm.id,
            sender=orm.sender,
            receiver=orm.receiver,
            content=orm.content,
            is_read=orm.is_read,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            read_at=orm.read_at
        )

    def save(self, message: SiteMessage) -> SiteMessage:
        if message.id is not None:
            orm_msg = self.db.query(SiteMessageORM).filter(SiteMessageORM.id == message.id).first()
            if orm_msg:
                orm_msg.sender = message.sender
                orm_msg.receiver = message.receiver
                orm_msg.content = message.content
                orm_msg.is_read = message.is_read
                orm_msg.created_at = message.created_at
                orm_msg.updated_at = message.updated_at
                orm_msg.read_at = message.read_at
                self.db.commit()
                return self._to_domain(orm_msg)
        
        orm_msg = SiteMessageORM(
            sender=message.sender,
            receiver=message.receiver,
            content=message.content,
            is_read=message.is_read,
            created_at=message.created_at,
            updated_at=message.updated_at,
            read_at=message.read_at
        )
        self.db.add(orm_msg)
        self.db.commit()
        self.db.refresh(orm_msg)
        message.id = orm_msg.id
        return message

    def find_by_id(self, message_id: int) -> Optional[SiteMessage]:
        orm_msg = self.db.query(SiteMessageORM).filter(SiteMessageORM.id == message_id).first()
        return self._to_domain(orm_msg) if orm_msg else None

    def find_by_receiver(self, receiver: str, status: str = "all") -> List[SiteMessage]:
        query = self.db.query(SiteMessageORM).filter(SiteMessageORM.receiver == receiver)
        if status == "unread":
            query = query.filter(SiteMessageORM.is_read == 0)
        elif status == "read":
            query = query.filter(SiteMessageORM.is_read == 1)
        
        orm_messages = query.order_by(SiteMessageORM.created_at.desc()).all()
        return [self._to_domain(msg) for msg in orm_messages]

    def mark_all_as_read(self, receiver: str) -> int:
        import datetime
        now = datetime.datetime.now()
        updated_count = self.db.query(SiteMessageORM).filter(
            SiteMessageORM.receiver == receiver,
            SiteMessageORM.is_read == 0
        ).update({
            SiteMessageORM.is_read: 1,
            SiteMessageORM.updated_at: now,
            SiteMessageORM.read_at: now
        }, synchronize_session=False)
        self.db.commit()
        return updated_count


class SQLUploadedFileRepository(UploadedFileRepository):
    """UploadedFileRepository 契约的 MySQL 具体实现"""

    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, orm: UploadedFileORM) -> UploadedFile:
        if not orm:
            return None
        return UploadedFile(
            id=orm.id,
            filename=orm.filename,
            file_path=orm.file_path,
            file_size_mb=orm.file_size_mb,
            created_at=orm.created_at
        )

    def save(self, uploaded_file: UploadedFile) -> UploadedFile:
        orm_file = self.db.query(UploadedFileORM).filter(UploadedFileORM.filename == uploaded_file.filename).first()
        if orm_file:
            orm_file.file_path = uploaded_file.file_path
            orm_file.file_size_mb = uploaded_file.file_size_mb
            orm_file.created_at = uploaded_file.created_at
            self.db.commit()
            return self._to_domain(orm_file)

        orm_file = UploadedFileORM(
            filename=uploaded_file.filename,
            file_path=uploaded_file.file_path,
            file_size_mb=uploaded_file.file_size_mb,
            created_at=uploaded_file.created_at
        )
        self.db.add(orm_file)
        self.db.commit()
        self.db.refresh(orm_file)
        uploaded_file.id = orm_file.id
        return uploaded_file

    def find_by_filename(self, filename: str) -> Optional[UploadedFile]:
        orm_file = self.db.query(UploadedFileORM).filter(UploadedFileORM.filename == filename).first()
        return self._to_domain(orm_file) if orm_file else None

    def find_all(self) -> List[UploadedFile]:
        orm_files = self.db.query(UploadedFileORM).order_by(UploadedFileORM.created_at.desc()).all()
        return [self._to_domain(f) for f in orm_files]

    def delete_by_id(self, file_id: int) -> Optional[UploadedFile]:
        orm_file = self.db.query(UploadedFileORM).filter(UploadedFileORM.id == file_id).first()
        if not orm_file:
            return None
        domain_file = self._to_domain(orm_file)
        self.db.delete(orm_file)
        self.db.commit()
        return domain_file



