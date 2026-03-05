def close_welcome():
    try:
        # Add your logic here
        pass
    except Exception as e:
        # Handle the exception
        db.session.rollback()  # Rollback the database session
        return jsonify({'error': str(e)}), 500
    finally:
        # Code that will run no matter what
        pass