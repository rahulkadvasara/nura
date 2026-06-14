// MongoDB initialization script for local development

// Switch to nura database
db = db.getSiblingDB('nura');

// Create collections with validation
db.createCollection("users", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["email", "password_hash", "full_name", "role"],
         properties: {
            email: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            password_hash: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            full_name: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            role: {
               enum: ["patient", "doctor", "admin"],
               description: "must be one of the enum values and is required"
            }
         }
      }
   }
});

// Create indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "role": 1 });

print("MongoDB initialized successfully for Nura development environment");