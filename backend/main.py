from flask import request, jsonify, session
from config import app, db
from models import Patient
from models import Visit
from models import Prescription
from models import User
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password_hash=generate_password_hash("adminpass"), role="admin")
        db.session.add(admin)
        db.session.commit()

#decorator to protect routes that require authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized. Please log in first."}),401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/check_session", methods=["GET"])
def check_session():
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        return jsonify({
            "logged_in": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }), 200
    return jsonify({"logged_in": False}), 401

@app.route('/create_user', methods=["POST"])
@login_required
def create_user():
    # current_user= db.session.get(User, session.get("user_id"))
    # if current_user.role !="admin":
    current_user = User.query.get(session["user_id"])
    if current_user.role != "admin":
        return jsonify({"error": "Forbidden. Admins only."}), 403
    
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")
    password_hash = generate_password_hash(password)
    if not username or not password_hash or not role:
        return jsonify({"message":"Missing data"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 400

    new_user = User(
        username=username, 
        password_hash=generate_password_hash(password), 
        role=role
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"message": "User created successfully"}), 201

@app.route('/users', methods=["GET"])
@login_required
def get_users():
    current_user= db.session.get(User, session.get("user_id"))
    if current_user.role !="admin":
        return jsonify({"error": "Forbidden. Admins only."}), 403
    users=User.query.all()
    json_users= list(map(lambda u: u.to_json(), users))
    return jsonify({"users": json_users}),200

@app.route('/delete_user/<int:user_id>', methods=["DELETE"])
@login_required
def delete_user(user_id):
    current_user= db.session.get(User, session.get("user_id"))  
    if current_user.role !="admin":
        return jsonify
    ({"error": "Forbidden. Admins only."}), 403
    user= db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}),404
    if user.id==current_user.id:
        return jsonify({"message": "You cannot delete yourself"}),400
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200

@app.route('/update_user/<int:user_id>', methods=["PATCH"])
@login_required
def update_user(user_id):
    current_user= db.session.get(User, session.get("user_id"))
    if current_user.role !="admin":
        return jsonify({"error": "Forbidden. Admins only."}), 403
    user= db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}),404
    data= request.json
    user.username=data.get("username", user.username)
    user.password_hash=data.get("passwordHash", user.password_hash)
    user.role=data.get("role", user.role)
    db.session.commit()
    return jsonify({"message": "User updated successfully"}), 200



#API route for user login


@app.route("/login", methods=["POST"])
def login():
    data=request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"message": "Missing username or password"}), 400

    user= User.query.filter_by(username=data["username"]).first()
 
    if user and check_password_hash(user.password_hash, data["password"]):
        session["user_id"] = user.id 
        return jsonify({"message": "login successful"}),200     
    else:
        return jsonify({"message": "Invalid credentials"}), 401



@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "logout successful"}), 200
    


@app.route("/patients/<int:patient_id>", methods=["GET"])
@login_required
def get_patient(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"message": "Patient not found"}), 404

    # Fetch related visits and prescriptions
    visits = Visit.query.filter_by(patient_id=patient_id).all()
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).all()

    return jsonify({
        "patient": patient.to_json(),
        "visits": [v.to_json() for v in visits],
        "prescriptions": [p.to_json() for p in prescriptions],
    }), 200


#API routes for paitent info

@app.route("/patients", methods=["GET"])
@login_required
def get_patients():
    patients=Patient.query.all()
    json_patients= list(map(lambda p: p.to_json(), patients))
    return jsonify({"patients": json_patients}),200

@app.route("/add_patient", methods=["POST"])
@login_required
def add_patient():
    data= request.get_json()
    first_name=data.get("firstName")
    last_name=data.get("lastName")
    email=data.get("email")
   

    if not first_name or not last_name or not email:
        return(
             jsonify({"message": "Missing data"}), 400
        )
    new_patient=Patient(first_name=first_name, last_name=last_name, email=email)
    try:
        db.session.add(new_patient)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    
    return jsonify({"message": "Patient added successfully"}), 201

@app.route("/update_patient/<int:patient_id>", methods=["PATCH"])
@login_required
def update_patient(patient_id):
    patient= db.session.get(Patient, patient_id)

    if not patient:
        return jsonify({"message": "Patient not found"}),404
    data= request.json
    patient.first_name=data.get("firstName", patient.first_name)
    patient.last_name=data.get("lastName", patient.last_name)
    patient.email=data.get("email", patient.email)

    db.session.commit()
    return jsonify({"message": "Patient updated successfully"}), 200

@app.route("/delete_patient/<int:patient_id>", methods=["DELETE"])
@login_required
def delete_patient(patient_id):
    patient= db.session.get(Patient, patient_id)

    if not patient:
        return jsonify({"message": "Patient not found"}),404

    db.session.delete(patient)
    db.session.commit()
    return jsonify({"message": "Patient deleted successfully"}), 200



#API routes for visits

@app.route("/visits", methods=["GET"])
@login_required
def get_visits():
    visits=Visit.query.all()
    json_visits= list(map(lambda v: v.to_json(), visits))
    return jsonify({"visits": json_visits}), 200


@app.route("/add_visit", methods=["POST"])
@login_required
def add_visit():
    data = request.get_json() 
    patient_id= data.get("patientId")
    visit_date = data.get("visitDate")
    reason=data.get("reason")

    if not patient_id or not visit_date or not reason:
        return jsonify({"message": "Missing data"}), 400
        
    try:
        visit_date=datetime.strptime(visit_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    patient= db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"message": "Patient not found"}), 404
    
    new_visit=Visit(patient_id=patient_id, visit_date=visit_date, reason=reason)
    try:
        db.session.add(new_visit)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    
    return jsonify({"message": "Visit added successfully"}), 201

@app.route("/update_visit/<int:visit_id>", methods=["PATCH"])
@login_required
def update_visit(visit_id):
    visit= db.session.get(Visit, visit_id)

    if not visit:
        return jsonify({"message": "Visit not found"}),404
    data= request.get_json()
    if "visitDate" in data:
        try:
            visit.visit_date = datetime.strptime(data["visitDate"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    visit.patient_id=data.get("patientId", visit.patient_id)
   
    visit.reason=data.get("reason", visit.reason)

    db.session.commit()
    return jsonify({"message": "Visit updated successfully"}), 200

@app.route("/delete_visit/<int:visit_id>", methods=["DELETE"])
@login_required
def delete_visit(visit_id):
    visit= db.session.get(Visit, visit_id)

    if not visit:
        return jsonify({"message": "Visit not found"}),404

    db.session.delete(visit)
    db.session.commit()
    return jsonify({"message": "Visit deleted successfully"}), 200

#API routes for prescriptions

@app.route("/prescriptions", methods=["GET"])
@login_required
def get_prescriptions():
    prescriptions=Prescription.query.all()
    json_prescriptions= list(map(lambda p: p.to_json(), prescriptions))
    return jsonify({"prescriptions": json_prescriptions})

@app.route("/add_prescription", methods=["POST"])
@login_required
def add_prescription():
    data= request.get_json()
    patient_id=data.get("patientId")
    medication_name=data.get("medicationName")
    dosage=data.get("dosage") 
    start_date = data.get("startDate")
    end_date = data.get("endDate")

    if not patient_id or not medication_name or not dosage or not start_date:
        return jsonify({"message": "Missing data"}), 400
    
    try:
        start_date=datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    patient= db.session.get(Patient, patient_id)
    if not patient:
        return jsonify({"message": "Patient not found"}), 404
    new_prescription=Prescription(patient_id=patient_id, medication_name=medication_name, dosage=dosage, start_date=start_date, end_date=end_date)
    try:
        db.session.add(new_prescription)
        db.session.commit()
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    
    return jsonify({"message": "Prescription added successfully"}), 201

@app.route("/update_prescription/<int:prescription_id>", methods=["PATCH"])
@login_required
def update_prescription(prescription_id):
    prescription= db.session.get(Prescription, prescription_id)

    if not prescription:
        return jsonify({"message": "Prescription not found"}),404
    data= request.json
    if "startDate" in data:
        try:
            prescription.start_date = datetime.strptime(data["startDate"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format for startDate. Use YYYY-MM-DD"}), 400
    if "endDate" in data:
        try:
            prescription.end_date = datetime.strptime(data["endDate"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format for endDate. Use YYYY-MM-DD"}), 400
    prescription.patient_id=data.get("patientId", prescription.patient_id)
    prescription.medication_name=data.get("medicationName", prescription.medication_name)
    prescription.dosage=data.get("dosage", prescription.dosage)
    db.session.commit()
    return jsonify({"message": "Prescription updated successfully"}), 200

@app.route("/delete_prescription/<int:prescription_id>", methods=["DELETE"])
@login_required
def delete_prescription(prescription_id):
    prescription= db.session.get(Prescription, prescription_id)

    if not prescription:
        return jsonify({"message": "Prescription not found"}),404

    db.session.delete(prescription)
    db.session.commit()
    return jsonify({"message": "Prescription deleted successfully"}), 200



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            default_user = User(
                username="admin",
                password_hash=generate_password_hash("adminpass"),
                role="admin"
            )
            db.session.add(default_user)
            db.session.commit()
            print("Database initialized and default admin user created.")
        else:
            print("Database already initialized.")
    app.run(debug=True,port=8080)