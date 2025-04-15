from website import create_app, db

app = create_app()

with app.app_context():
    try:
        db.drop_all()
        print("✅ Dropped all existing tables")
        
        db.create_all()
        print("✅ Created new tables with updated schema")
        
    except Exception as e:
        print("❌ An error occurred:", e)