from application import app

# run the application!
if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = app.config['PORT']
    app.run(host='0.0.0.0', port=port)
