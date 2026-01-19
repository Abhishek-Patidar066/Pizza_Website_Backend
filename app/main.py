from enum import Enum
from typing import Annotated, Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from sqlitedict import SqliteDict


app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "pizza_dev.db"

# ---------------------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------------------
def get_db():
    db = SqliteDict(DB_PATH)
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------
# Get Order by Name
# ---------------------------------------------------------------------
@app.get("/Order/by-name/{name}")
def get_pizza(name: str, db: Dict = Depends(get_db)):
    with db as DB:
        for pizza in DB.values():
            if pizza["name"] == name:
                return pizza

    raise HTTPException(status_code=404, detail="Pizza not found")


# ---------------------------------------------------------------------
# Get Order by ID
# ---------------------------------------------------------------------
@app.get("/Order/by-id/{item_id}")
def get_order(item_id: int, db: Dict = Depends(get_db)):
    with db as DB:
        pizza = DB.get(str(item_id))
        if pizza:
            return pizza

    raise HTTPException(status_code=404, detail="Order not found")


# ---------------------------------------------------------------------
# Place Order
# ---------------------------------------------------------------------
class Order(BaseModel):
    id: int
    quantity: Annotated[int, Field(ge=1)]


@app.post("/place_order/")
def place_order(order: List[Order], db: Dict = Depends(get_db)):
    total_price = 0.0
    order_details = []
    unavailable_items = []
    ccid = uuid4()

    with db as DB:
        for item in order:
            pizza = DB.get(str(item.id))

            if pizza:
                item_total = pizza["price"] * item.quantity
                total_price += item_total
                order_details.append(
                    {
                        "pizza": pizza["name"],
                        "quantity": item.quantity,
                        "item_total": item_total,
                    }
                )
            else:
                unavailable_items.append(item.id)

    if not order_details:
        raise HTTPException(
            status_code=404,
            detail="None of the requested items are available",
        )

    return {
        "Order_id": str(ccid),
        "order_details": order_details,
        "total_price": total_price,
        "unavailable_items": unavailable_items
    }


# ---------------------------------------------------------------------
# Create / Add Pizza
# ---------------------------------------------------------------------
class PizzaSize(str, Enum):
    small = "Small"
    medium = "Medium"
    large = "Large"


class Addpizza(BaseModel):
    id: Annotated[int, Field(ge=0)]
    name: str
    size: PizzaSize
    price: Annotated[float, Field(gt=0)]
    toppings: List[str]


@app.post("/add_pizza/")
def add_pizza(pizza: Addpizza, db: Dict = Depends(get_db)):
    with db as DB:
        pizza_id = str(pizza.id)

        if pizza_id in DB:
            raise HTTPException(
                status_code=409,
                detail="Pizza with this ID already exists",
            )

        DB[pizza_id] = pizza.model_dump()
        DB.commit()

    return {
        "message": "Pizza added successfully",
        "pizza": pizza.model_dump(),
    }


# ---------------------------------------------------------------------
# Update Pizza
# ---------------------------------------------------------------------
class Updatepizza(BaseModel):
    name: Optional[str] = None
    size: Optional[str] = None
    price: Optional[float] = None
    toppings: Optional[List[str]] = None


@app.patch("/update_pizza/{pizza_id}")
def update_pizza(
    pizza_id: int,
    pizza: Updatepizza,
    db: Dict = Depends(get_db),
):
    with db as DB:
        pizza_key = str(pizza_id)

        if pizza_key not in DB:
            raise HTTPException(status_code=404, detail="Pizza not found")

        existing_pizza = DB[pizza_key]
        updated_pizza = existing_pizza.copy()

        for field, value in pizza.model_dump(exclude_unset=True).items():
            updated_pizza[field] = value

        DB[pizza_key] = updated_pizza
        DB.commit()

    return {
        "message": "Pizza updated successfully",
        "pizza": updated_pizza,
    }


# ---------------------------------------------------------------------
# Delete Pizza
# ---------------------------------------------------------------------
class DeletePizzaRequest(BaseModel):
    pizza_ids: List[int]


@app.delete("/delete_pizzas")
def delete_pizzas(
    request: DeletePizzaRequest,
    db: Dict = Depends(get_db),
):
    deleted_ids = []
    not_found_ids = []

    with db as DB:
        for pid in request.pizza_ids:
            key = str(pid)

            if key in DB:
                del DB[key]
                deleted_ids.append(pid)
            else:
                not_found_ids.append(pid)

        DB.commit()

    if not_found_ids:
        return {
            "message": "Some pizzas were deleted, some were not found",
            "deleted": deleted_ids,
            "not_found": not_found_ids,
        }

    return {
        "message": "All pizzas deleted successfully",
        "deleted": deleted_ids,
    }
