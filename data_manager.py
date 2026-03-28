import json
import os
from datetime import datetime
from config_data import OBJECTS, USERS
from stock_data import CURRENT_STOCK

class DataManager:
    DATA_FILE = "gas_data.json"
    USERS_FILE = "users.json"
    
    def __init__(self):
        self.data = self.load_data()
        self.users = self.load_users()
    
    def load_data(self):
        if os.path.exists(self.DATA_FILE):
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return self.get_default_data()
    
    def get_default_data(self):
        # Создаем объекты с остатками из CURRENT_STOCK
        objects_list = []
        
        for obj in OBJECTS:
            stock_item = next((item for item in CURRENT_STOCK if item[0] == obj["id"]), None)
            
            if stock_item:
                objects_list.append({
                    "id": obj["id"],
                    "name": obj["name"],
                    "oxygen": stock_item[1],
                    "propane": stock_item[2]
                })
            else:
                objects_list.append({
                    "id": obj["id"],
                    "name": obj["name"],
                    "oxygen": 0,
                    "propane": 0
                })
        
        return {
            "objects": objects_list,
            "requests": [],
            "deliveries": []
        }
    
    def load_users(self):
        if os.path.exists(self.USERS_FILE):
            with open(self.USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return self.get_default_users()
    
    def get_default_users(self):
        return USERS
    
    def save_data(self):
        with open(self.DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def save_users(self):
        with open(self.USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def add_request(self, object_id, gas_type, quantity, user_name):
        request = {
            "id": len(self.data["requests"]) + 1,
            "object_id": object_id,
            "gas_type": gas_type,
            "quantity": quantity,
            "status": "active",
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "created_by": user_name
        }
        self.data["requests"].append(request)
        self.save_data()
        return request
    
    def get_master_requests(self, master_name):
        """Получить все заявки мастера"""
        return [r for r in self.data["requests"] if r["created_by"] == master_name and r["status"] == "active"]
    
    def clear_master_requests(self, master_name, object_id, gas_type):
        """Удалить старые заявки мастера перед новой"""
        self.data["requests"] = [
            r for r in self.data["requests"] 
            if not (r["created_by"] == master_name 
                   and r["object_id"] == object_id 
                   and r["gas_type"] == gas_type 
                   and r["status"] == "active")
        ]
        self.save_data()
    
    def add_delivery(self, object_id, gas_type, quantity, planned_date, supplier_name):
        delivery = {
            "id": len(self.data["deliveries"]) + 1,
            "object_id": object_id,
            "gas_type": gas_type,
            "quantity": quantity,
            "status": "planned",
            "planned_date": planned_date,
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "created_by": supplier_name
        }
        self.data["deliveries"].append(delivery)
        self.save_data()
        return delivery
    
    def complete_delivery(self, delivery_id, completer_name):
        for delivery in self.data["deliveries"]:
            if delivery["id"] == delivery_id and delivery["status"] == "planned":
                delivery["status"] = "completed"
                delivery["completed_at"] = datetime.now().strftime("%d.%m.%Y %H:%M")
                
                # Обновляем остатки на объекте (прибавляем то, что завезли)
                for obj in self.data["objects"]:
                    if obj["id"] == delivery["object_id"]:
                        if delivery["gas_type"] == "КИСЛОРОД":
                            obj["oxygen"] += delivery["quantity"]
                        else:
                            obj["propane"] += delivery["quantity"]
                        
                        # УМЕНЬШАЕМ заявки на то, что завезли
                        for req in self.data["requests"]:
                            if (req["object_id"] == delivery["object_id"] 
                                and req["gas_type"] == delivery["gas_type"]
                                and req["status"] == "active"):
                                req["quantity"] -= delivery["quantity"]
                        
                        # Удаляем только те заявки, которые стали 0 или меньше
                        self.data["requests"] = [
                            r for r in self.data["requests"] 
                            if not (r["object_id"] == delivery["object_id"] 
                                   and r["gas_type"] == delivery["gas_type"]
                                   and r["quantity"] <= 0)
                        ]
                        break
                self.save_data()
                return True
        return False
    
    def get_objects_for_master(self, master_id):
        """Получить все объекты мастера"""
        for master in self.users["masters"]:
            if master["id"] == master_id:
                return [obj for obj in self.data["objects"] if obj["id"] in master["objects"]]
        return []
    
    def get_all_objects(self):
        return self.data["objects"]
    
    def get_active_requests(self, object_id=None):
        if object_id:
            return [r for r in self.data["requests"] if r["object_id"] == object_id and r["status"] == "active"]
        return [r for r in self.data["requests"] if r["status"] == "active"]
    
    def get_planned_deliveries(self, object_id=None):
        if object_id:
            return [d for d in self.data["deliveries"] if d["object_id"] == object_id and d["status"] == "planned"]
        return [d for d in self.data["deliveries"] if d["status"] == "planned"]
    
    def update_oxygen(self, object_id, value):
        for obj in self.data["objects"]:
            if obj["id"] == object_id:
                obj["oxygen"] = value
                self.save_data()
                return True
        return False
    
    def update_propane(self, object_id, value):
        for obj in self.data["objects"]:
            if obj["id"] == object_id:
                obj["propane"] = value
                self.save_data()
                return True
        return False