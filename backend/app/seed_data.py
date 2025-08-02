from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.product import Category

def create_initial_categories():
    """Create initial product categories."""
    db = SessionLocal()
    try:
        categories = [
            {
                "name": "Vegetables",
                "name_ja": "野菜",
                "name_ne": "तरकारी",
                "description": "Fresh vegetables and greens",
                "icon": "🥬"
            },
            {
                "name": "Fruits",
                "name_ja": "果物",
                "name_ne": "फलफूल",
                "description": "Fresh seasonal fruits",
                "icon": "🍎"
            },
            {
                "name": "Herbs & Spices",
                "name_ja": "ハーブ・スパイス",
                "name_ne": "जडिबुटी र मसला",
                "description": "Fresh herbs and dried spices",
                "icon": "🌿"
            },
            {
                "name": "Grains & Cereals",
                "name_ja": "穀物",
                "name_ne": "अनाज",
                "description": "Rice, wheat, and other grains",
                "icon": "🌾"
            },
            {
                "name": "Dairy Products",
                "name_ja": "乳製品",
                "name_ne": "दूध उत्पादन",
                "description": "Fresh milk, cheese, and dairy",
                "icon": "🥛"
            },
            {
                "name": "Meat & Poultry",
                "name_ja": "肉類",
                "name_ne": "मासु",
                "description": "Fresh meat and poultry products",
                "icon": "🥩"
            }
        ]
        
        for cat_data in categories:
            existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if not existing:
                category = Category(**cat_data)
                db.add(category)
        
        db.commit()
        print("Initial categories created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating categories: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_categories()