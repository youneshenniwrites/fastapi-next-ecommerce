from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

def get_products(db: Session, skip: int = 0, limit: int = 10) -> List[Product]:
    return db.query(Product).offset(skip).limit(limit).all()

def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()

def create_product(db: Session, obj_in: ProductCreate) -> Product:
    db_obj = Product(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
  
def update_product(db: Session, db_obj: Product, obj_in: ProductUpdate) -> Product:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_product(db: Session, db_obj: Product) -> None:
    db.delete(db_obj)
    db.commit()