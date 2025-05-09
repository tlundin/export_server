from flask import Flask, request, Response, jsonify, Blueprint, send_from_directory
import datetime
import logging
import os
from random import randrange

bp = Blueprint('export_api',__name__,url_prefix='/')

# In-memory storage for the latest position of each team member
# Structure: { "user_uuid": {"name": "User Name", "position": {"easting": 0.0, "northing": 0.0}, "timestamp": "ISO8601_string"}, ... }
team_positions = {}

# Endpoint to retrieve server updates - change here indicates a new version of the server
@bp.route("/server",methods=['GET'])
def server_update():
    version = ''
    logging.info('GET /server')
    return jsonify({"version": randrange(10)})

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

# Ensure these directories exist or the save operations will fail
IMG_UPLOAD_FOLDER = '/flaskAppServer/images'
FILE_UPLOAD_FOLDER = '/flaskAppServer/files'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'json'}

# Create directories if they don't exist
os.makedirs(IMG_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FILE_UPLOAD_FOLDER, exist_ok=True)


@bp.route('/upload', methods=['POST'])
def upload_img():
    if request.method == 'POST':
        # Iterate through all files in the request
        for filename in request.files:
            file = request.files[filename]
            # Check if a file was actually submitted for this filename key
            if file.filename == '':
                continue # Skip if no file was selected for this input

            if allowed_file(file.filename):
                print("name", file.filename)
                print("type", file.content_type)
                # Note: file.content_length is not reliable with Werkzeug/Flask request.files
                # print("size", file.content_length)
                logging.info(f"File: {file.filename} Type: {file.content_type}")

                try:
                    if file.content_type and file.content_type.startswith("image"):
                        file.save(os.path.join(IMG_UPLOAD_FOLDER, file.filename))
                        logging.info(f"Saved image: {file.filename}")
                    else:
                        file.save(os.path.join(FILE_UPLOAD_FOLDER, file.filename))
                        logging.info(f"Saved file: {file.filename}")
                except Exception as e:
                    logging.error(f"Error saving file {file.filename}: {e}")
                    return Response(f'Error saving file {file.filename}', 500)
            else:
                return Response(f'Filename {file.filename} is not allowed', 400) # Use 400 for bad request due to disallowed file type

        # Check if any files were processed
        if not request.files:
             return Response('No files provided in the request', 400)

        return Response("Upload successful", 200)
    return Response('Method not allowed', 405) # Use 405 for method not allowed


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/files",methods=['GET'])
def _list_files():
    logging.info('GET /files')
    return list_files_in_folder(FILE_UPLOAD_FOLDER)


@bp.route("/images",methods=['GET'])
def list_images():
    logging.info('GET /images')
    return list_files_in_folder(IMG_UPLOAD_FOLDER)

def list_files_in_folder(folder):
    """Helper function to list files in a given folder."""
    try:
        from os import listdir
        from os.path import isfile, join
        onlyfiles = [f for f in listdir(folder) if isfile(join(folder, f))]
        return str(onlyfiles)
    except FileNotFoundError:
        return Response(f"Folder not found: {folder}", 404)
    except Exception as e:
        logging.error(f"Error listing files in {folder}: {e}")
        return Response("Error listing files", 500)


@bp.route("/files/<path:name>")
def download_file(name):
    logging.info(f'GET /files/{name}')
    try:
        return send_from_directory(
            FILE_UPLOAD_FOLDER, name, as_attachment=True
        )
    except FileNotFoundError:
        return Response("File not found", 404)
    except Exception as e:
        logging.error(f"Error serving file {name}: {e}")
        return Response("Error serving file", 500)


@bp.route("/images/<path:name>")
def download_image(name):
    logging.info(f'GET /images/{name}')
    try:
        return send_from_directory(
            IMG_UPLOAD_FOLDER, name, as_attachment=True
        )
    except FileNotFoundError:
        return Response("Image not found", 404)
    except Exception as e:
        logging.error(f"Error serving image {name}: {e}")
        return Response("Error serving image", 500)

@bp.route("/images", methods=['DELETE'])
def delete_all_images():
    """Deletes all files in the image upload folder."""
    logging.info('DELETE /images')
    try:
        from os import listdir, remove
        from os.path import isfile, join

        files_to_delete = [f for f in listdir(IMG_UPLOAD_FOLDER) if isfile(join(IMG_UPLOAD_FOLDER, f))]

        if not files_to_delete:
            return Response("No images found to delete", 200) # Or 404, depending on desired behavior when no files exist

        deleted_count = 0
        for filename in files_to_delete:
            try:
                os.remove(os.path.join(IMG_UPLOAD_FOLDER, filename))
                logging.info(f"Deleted image: {filename}")
                deleted_count += 1
            except OSError as e:
                logging.error(f"Error deleting image {filename}: {e}")
                # Continue with other files even if one fails

        return Response(f"Deleted {deleted_count} images", 200)

    except FileNotFoundError:
        # This case should be less likely with os.makedirs(exist_ok=True) but good to handle
        return Response(f"Image folder not found: {IMG_UPLOAD_FOLDER}", 500)
    except Exception as e:
        logging.error(f"Error deleting all images: {e}")
        return Response("Error deleting images", 500)
