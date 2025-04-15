from website import create_app, db

app = create_app()

with app.app_context():
    try:
        db.create_all()
        print("✅ Database connection successful!")
        print("✅ All tables created!")
    except Exception as e:
        print("❌ An error occurred:", e)