from sqlalchemy.orm import Session

from iip_search import crud
from iip_search import models
from iip_search import schemas


def list_inscriptions_by_display_status(
    db: Session, display_status: schemas.DisplayStatus
):
    return db.query(models.Inscription).where(
        models.Inscription.display_status == display_status
    )


def update_inscription(db: Session, slug: str, inscription: schemas.InscriptionPatch):
    to_update = db.query(models.Inscription).filter_by(filename=f"{slug}.xml").one()
    to_update.display_status = inscription.display_status

    db.commit()

    return crud.get_inscription(db, slug)
