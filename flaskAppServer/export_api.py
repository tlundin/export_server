
from flask import Flask, request, Response, jsonify, Blueprint, send_from_directory
import datetime
import logging

bp = Blueprint('export_api',__name__,url_prefix='/')

# In-memory storage for the latest position of each team member
# Structure: { "user_uuid": {"name": "User Name", "position": {"easting": 0.0, "northing": 0.0}, "timestamp": "ISO8601_string"}, ... }
team_positions = {}

# Endpoint to receive position updates from team members
@bp.route('/position', methods=['POST'])
def update_position():
    """
    Receives a JSON payload with a team member's position update using SWEREF coordinates.
    Stores/overwrites the latest position data for that member.
    Expected JSON payload:
    {
        "uuid": "unique-user-identifier",
        "name": "User Name",
        "position": {
            "easting": 674000.0,  # Example SWEREF 99 TM Easting
            "northing": 6580000.0 # Example SWEREF 99 TM Northing
        },
        "timestamp": "2025-03-27T10:30:00Z" # ISO 8601 format recommended
    }
    """
    data = request.get_json()

    # Basic validation
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    required_fields = ["uuid", "name", "position", "timestamp"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    position_data = data.get("position")
    # Validate position object structure and coordinate keys
    if not isinstance(position_data, dict) or "easting" not in position_data or "northing" not in position_data:
        return jsonify({"error": "Invalid or missing 'position' object with 'easting' and 'northing'"}), 400

    # Validate coordinate values are numbers
    if not isinstance(position_data["easting"], (int, float)) or not isinstance(position_data["northing"], (int, float)):
         return jsonify({"error": "'easting' and 'northing' must be numeric values"}), 400

    # Extract data
    user_uuid = data["uuid"]
    user_name = data["name"]
    user_position = data["position"] # Contains {"easting": ..., "northing": ...}
    user_timestamp = data["timestamp"]

    # TODO Optional: Add timestamp validation/parsing if needed
    # try:
    #     datetime.datetime.fromisoformat(user_timestamp.replace('Z', '+00:00')) # Example parsing
    # except ValueError:
    #     return jsonify({"error": "Invalid timestamp format. Please use ISO 8601 format."}), 400

    # Update the in-memory dictionary (overwrites previous entry for the same uuid)
    team_positions[user_uuid] = {
        "name": user_name,
        "position": user_position,
        "timestamp": user_timestamp
    }

    print(f"Updated SWEREF position for {user_name} ({user_uuid})") # Optional: Server log
    return jsonify({"status": "success", "message": f"Position updated for {user_uuid}"}), 200

# Endpoint to retrieve the current positions of all team members
@bp.route('/positions', methods=['GET'])
def get_all_positions():
    """
    Returns a JSON object containing the latest known SWEREF position
    for all tracked team members.
    Response structure:
    [
      {
        "uuid": "unique-user-identifier",
        "name": "User Name",
        "position": { "easting": 0.0, "northing": 0.0 },
        "timestamp": "ISO8601_string"
      },
      ...
    ]
    """
    # Convert the dictionary storage to the desired list format
    current_positions_list = []
    for uuid, data in team_positions.items():
        current_positions_list.append({
            "uuid": uuid,
            "name": data["name"],
            "position": data["position"], # Contains {"easting": ..., "northing": ...}
            "timestamp": data["timestamp"]
        })

    return jsonify(current_positions_list), 200

@bp.route('/')
def greeting():
    logging.info('GET /greeting')
    return 'Hello this message is coming from the Teraim app server'

IMG_UPLOAD_FOLDER = '/flaskAppServer/images'
FILE_UPLOAD_FOLDER = '/flaskAppServer/files'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'json'}

@bp.route('/upload', methods=['POST'])
def upload_img():
    if request.method == 'POST':
        for filename in request.files:
            if allowed_file(filename):
                file = request.files[filename]
                print("name", file.filename)
                print("type", file.content_type)
                print("size", file.content_length)
                logging.info("File: {} Size: {}".format(file.filename,file.content_length));
                if file.content_type.startswith("image"):
                    file.save(IMG_UPLOAD_FOLDER + "/" + filename)
                else:
                    file.save(FILE_UPLOAD_FOLDER + "/" + filename)
            else:
                return Response('filename {} is not allowed'.format(filename), 403)
        return Response("OK")
    return Response('method not allowed',404)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/files",methods=['GET'])
def _list_files():
    logging.info('GET /files')
    return list_files(FILE_UPLOAD_FOLDER)


@bp.route("/images",methods=['GET'])
def list_files(folder=IMG_UPLOAD_FOLDER):
    logging.info('GET /images')
    from os import listdir
    from os.path import isfile, join
    onlyfiles = [f for f in listdir(folder) if isfile(join(folder, f))]
    return str(onlyfiles)


@bp.route("/files/<path:name>")
def download_file(name):
    logging.info('GET /files/{}'.format(name))
    return send_from_directory(
        FILE_UPLOAD_FOLDER, name, as_attachment=True
    )


@bp.route("/images/<path:name>")
def download_image(name):
    logging.info('GET /images/{}'.format(name))
    return send_from_directory(
        IMG_UPLOAD_FOLDER, name, as_attachment=True
    )

