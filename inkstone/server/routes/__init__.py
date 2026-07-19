def register_blueprints(app):
    from routes.auth import auth_bp
    from routes.write import write_bp
    from routes.works import works_bp
    from routes.community import community_bp
    from routes.interactions import interactions_bp
    from routes.stats import stats_bp
    from routes.graph import graph_bp
    from routes.challenges import challenges_bp
    from routes.users import users_bp
    from routes.notifications import notifications_bp
    from routes.review import review_bp
    from routes.poems import poems_bp
    from routes.materials import materials_bp
    from routes.daily import daily_bp
    from routes.rankings import rankings_bp
    from routes.serialize import serialize_bp
    from routes.rp import rp_bp
    from routes.library import library_bp
    from routes.bookshelf import bookshelf_bp
    from routes.reading import reading_bp
    from routes.bookmarks import bookmarks_bp
    from routes.annotations import annotations_bp
    from routes.checkin import checkin_bp
    from routes.report import report_bp
    from routes.highlights import highlights_bp
    from routes.reviews import reviews_bp
    from routes.compare import compare_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(write_bp, url_prefix='/api/write')
    app.register_blueprint(works_bp, url_prefix='/api/works')
    app.register_blueprint(community_bp, url_prefix='/api/community')
    app.register_blueprint(interactions_bp, url_prefix='/api/interactions')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(challenges_bp, url_prefix='/api/challenges')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(review_bp, url_prefix='/api/review')
    app.register_blueprint(poems_bp, url_prefix='/api/poems')
    app.register_blueprint(materials_bp, url_prefix='/api/materials')
    app.register_blueprint(daily_bp, url_prefix='/api/daily')
    app.register_blueprint(rankings_bp, url_prefix='/api/rankings')
    app.register_blueprint(serialize_bp, url_prefix='/api/serialize')
    app.register_blueprint(rp_bp, url_prefix='/api/rp')
    app.register_blueprint(library_bp, url_prefix='/api/library')
    app.register_blueprint(bookshelf_bp, url_prefix='/api/bookshelf')
    app.register_blueprint(reading_bp, url_prefix='/api/reading')
    app.register_blueprint(bookmarks_bp, url_prefix='/api/bookmarks')
    app.register_blueprint(annotations_bp, url_prefix='/api/annotations')
    app.register_blueprint(checkin_bp, url_prefix='/api/reading/checkin')
    app.register_blueprint(report_bp, url_prefix='/api/reading/report')
    app.register_blueprint(highlights_bp, url_prefix='/api/highlights')
    app.register_blueprint(reviews_bp, url_prefix='/api/library/reviews')
    app.register_blueprint(compare_bp, url_prefix='/api/compare')
