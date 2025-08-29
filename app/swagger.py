# app/swagger.py
swagger_spec = {
  "swagger": "2.0",
  "info": {
    "title": "Mechanic Shop API",
    "version": "1.0.0",
    "description": "CRUD for customers, mechanics, inventory, service tickets + auth, rate-limits, and caching."
  },
  "basePath": "/",
  "schemes": ["https"],
  "consumes": ["application/json"],
  "produces": ["application/json"],

  # --- Auth defs ---
  "securityDefinitions": {
    "BearerAuth": {
      "type": "apiKey",
      "name": "Authorization",
      "in": "header",
      "description": "Use: Bearer <JWT>"
    }
  },
  # Apply Bearer to everything by default; override with [] on public routes.
  "security": [{"BearerAuth": []}],

  "tags": [
    {"name": "Auth", "description": "Login & tokens"},
    {"name": "Customers", "description": "Customer CRUD"},
    {"name": "Mechanics", "description": "Mechanic CRUD & views"},
    {"name": "ServiceTickets", "description": "Tickets & assignments"},
    {"name": "Inventory", "description": "Parts inventory & linking"}
  ],

  "paths": {
    # ---------- AUTH ----------
    "/login": {
      "post": {
        "tags": ["Auth"],
        "summary": "Customer login",
        "description": "Validates customer credentials and returns a JWT.",
        "security": [],  # public
        "parameters": [
          {"in": "body", "name": "credentials", "schema": {"$ref": "#/definitions/LoginRequest"}, "required": True}
        ],
        "responses": {
          "200": {"description": "Token issued", "schema": {"$ref": "#/definitions/AuthToken"}},
          "401": {"description": "Invalid credentials", "schema": {"$ref": "#/definitions/Error"}}
        }
      }
    },
    "/mechanics/login": {
      "post": {
        "tags": ["Auth"],
        "summary": "Mechanic login",
        "description": "Validates mechanic credentials and returns a JWT.",
        "security": [],  # public
        "parameters": [
          {"in": "body", "name": "credentials", "schema": {"$ref": "#/definitions/LoginRequest"}, "required": True}
        ],
        "responses": {
          "200": {"description": "Token issued", "schema": {"$ref": "#/definitions/AuthToken"}},
          "401": {"description": "Invalid credentials", "schema": {"$ref": "#/definitions/Error"}}
        }
      }
    },

    # ---------- CUSTOMERS ----------
    "/customers/": {
      "get": {
        "tags": ["Customers"],
        "summary": "List customers",
        "responses": {
          "200": {"description": "OK", "schema": {"type": "array", "items": {"$ref": "#/definitions/Customer"}}}
        }
      },
      "post": {
        "tags": ["Customers"],
        "summary": "Create customer",
        "parameters": [
          {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/CustomerCreate"}, "required": True}
        ],
        "responses": {
          "201": {"description": "Created", "schema": {"$ref": "#/definitions/Customer"}},
          "400": {"description": "Validation error", "schema": {"$ref": "#/definitions/Error"}}
        }
      }
    },
    "/customers/{id}": {
      "get": {
        "tags": ["Customers"], "summary": "Get customer by id",
        "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}],
        "responses": {"200": {"schema": {"$ref": "#/definitions/Customer"}}, "404": {"$ref": "#/definitions/NotFound"}}
      },
      "put": {
        "tags": ["Customers"], "summary": "Update customer",
        "parameters": [
          {"name": "id", "in": "path", "required": True, "type": "integer"},
          {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/CustomerUpdate"}, "required": True}
        ],
        "responses": {"200": {"schema": {"$ref": "#/definitions/Customer"}}, "400": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}
      },
      "delete": {
        "tags": ["Customers"], "summary": "Delete customer",
        "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}],
        "responses": {"204": {"description": "Deleted"}, "404": {"$ref": "#/definitions/NotFound"}}
      }
    },

    # ---------- MECHANICS ----------
    "/mechanics/": {
      "get": {
        "tags": ["Mechanics"], "summary": "List mechanics",
        "responses": {"200": {"schema": {"type": "array", "items": {"$ref": "#/definitions/Mechanic"}}}}
      },
      "post": {
        "tags": ["Mechanics"], "summary": "Create mechanic",
        "parameters": [{"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/MechanicCreate"}, "required": True}],
        "responses": {"201": {"schema": {"$ref": "#/definitions/Mechanic"}}, "400": {"$ref": "#/definitions/Error"}}
      }
    },
    "/mechanics/{id}": {
      "get": {
        "tags": ["Mechanics"], "summary": "Get mechanic",
        "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}],
        "responses": {"200": {"schema": {"$ref": "#/definitions/Mechanic"}}, "404": {"$ref": "#/definitions/NotFound"}}
      },
      "put": {
        "tags": ["Mechanics"], "summary": "Update mechanic",
        "parameters": [
          {"name": "id", "in": "path", "required": True, "type": "integer"},
          {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/MechanicUpdate"}, "required": True}
        ],
        "responses": {"200": {"schema": {"$ref": "#/definitions/Mechanic"}}, "400": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}
      },
      "delete": {
        "tags": ["Mechanics"], "summary": "Delete mechanic",
        "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}],
        "responses": {"204": {"description": "Deleted"}, "404": {"$ref": "#/definitions/NotFound"}}
      }
    },
    "/mechanic/my-assigned-tickets": {
      "get": {
        "tags": ["Mechanics"],
        "summary": "Tickets assigned to the logged-in mechanic",
        "responses": {
          "200": {"schema": {"type": "array", "items": {"$ref": "#/definitions/ServiceTicket"}}},
          "401": {"$ref": "#/definitions/Error"}
        }
      }
    },

    # ---------- INVENTORY ----------
    "/inventory/": {
      "get": {"tags": ["Inventory"], "summary": "List parts", "responses": {"200": {"schema": {"type": "array", "items": {"$ref": "#/definitions/InventoryItem"}}}}},
      "post": {"tags": ["Inventory"], "summary": "Create part", "parameters": [{"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/InventoryCreate"}, "required": True}], "responses": {"201": {"schema": {"$ref": "#/definitions/InventoryItem"}}, "400": {"$ref": "#/definitions/Error"}}}
    },
    "/inventory/{id}": {
      "get": {"tags": ["Inventory"], "summary": "Get part", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"200": {"schema": {"$ref": "#/definitions/InventoryItem"}}, "404": {"$ref": "#/definitions/NotFound"}}},
      "put": {"tags": ["Inventory"], "summary": "Update part", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}, {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/InventoryUpdate"}, "required": True}], "responses": {"200": {"schema": {"$ref": "#/definitions/InventoryItem"}}, "400": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}},
      "delete": {"tags": ["Inventory"], "summary": "Delete part", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"204": {"description": "Deleted"}, "404": {"$ref": "#/definitions/NotFound"}}}
    },

    # ---------- SERVICE TICKETS ----------
    "/service_tickets/": {
      "get": {
        "tags": ["ServiceTickets"],
        "summary": "List service tickets",
        "responses": {"200": {"schema": {"type": "array", "items": {"$ref": "#/definitions/ServiceTicket"}}}, "401": {"$ref": "#/definitions/Error"}}
      },
      "post": {
        "tags": ["ServiceTickets"],
        "summary": "Create ticket",
        "description": "Create a new service ticket for a vehicle. Provide `vin` or `vehicle_id`.",
        "parameters": [{"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/ServiceTicketCreate"}, "required": True}],
        "responses": {"201": {"schema": {"$ref": "#/definitions/ServiceTicket"}}, "400": {"$ref": "#/definitions/Error"}, "401": {"$ref": "#/definitions/Error"}}
      }
    },
    "/service_tickets/{id}": {
      "get": {"tags": ["ServiceTickets"], "summary": "Get ticket", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"200": {"schema": {"$ref": "#/definitions/ServiceTicket"}}, "401": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}},
      "put": {"tags": ["ServiceTickets"], "summary": "Update ticket", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}, {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/ServiceTicketUpdate"}, "required": True}], "responses": {"200": {"schema": {"$ref": "#/definitions/ServiceTicket"}}, "400": {"$ref": "#/definitions/Error"}, "401": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}},
      "delete": {"tags": ["ServiceTickets"], "summary": "Delete ticket", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"204": {"description": "Deleted"}, "401": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}}
    },
    "/service_tickets/{id}/assign": {
      "post": {
        "tags": ["ServiceTickets"],
        "summary": "Assign mechanics/parts to ticket",
        "parameters": [
          {"name": "id", "in": "path", "required": True, "type": "integer"},
          {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/TicketAssignmentUpdate"}, "required": True}
        ],
        "responses": {"200": {"schema": {"$ref": "#/definitions/ServiceTicket"}}, "400": {"$ref": "#/definitions/Error"}, "401": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}
      }
    }
  },

  "definitions": {
    "Error": {"type": "object", "properties": {"error": {"type": "string"}}},
    "NotFound": {"type": "object", "properties": {"error": {"type": "string", "example": "Not found"}}},

    "LoginRequest": {
      "type": "object",
      "required": ["email", "password"],
      "properties": {"email": {"type": "string", "format": "email"}, "password": {"type": "string", "format": "password"}}
    },
    "AuthToken": {"type": "object", "properties": {"token": {"type": "string"}}},

    "Customer": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "address": {"type": "string"},
        "phone": {"type": "string"},
        "email": {"type": "string", "format": "email"}
      }
    },
    # Keep required minimal to match your schema/routes (email+password enough)
    "CustomerCreate": {
      "type": "object",
      "required": ["email", "password"],
      "properties": {
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "address": {"type": "string"},
        "phone": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "password": {"type": "string", "format": "password"}
      }
    },
    "CustomerUpdate": {
      "type": "object",
      "properties": {
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "address": {"type": "string"},
        "phone": {"type": "string"},
        "email": {"type": "string", "format": "email"}
      }
    },

    "Mechanic": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"},
        "address": {"type": "string"},
        "salary": {"type": "number"}
      }
    },
    "MechanicCreate": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"},
        "address": {"type": "string"},
        "salary": {"type": "number"},
        "password": {"type": "string", "format": "password"}
      }
    },
    "MechanicUpdate": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"},
        "address": {"type": "string"},
        "salary": {"type": "number"},
        "password": {"type": "string", "format": "password"}
      }
    },

    "InventoryItem": {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}, "price": {"type": "number"}}},
    "InventoryCreate": {"type": "object", "required": ["name", "price"], "properties": {"name": {"type": "string"}, "price": {"type": "number"}}},
    "InventoryUpdate": {"type": "object", "properties": {"name": {"type": "string"}, "price": {"type": "number"}}},

    "ServiceTicket": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "vin": {"type": "string"},
        "description": {"type": "string"},
        "status": {"type": "string", "enum": ["open", "in_progress", "closed"]},
        "total_cost": {"type": "number"},
        "date_in": {"type": "string", "format": "date-time"},
        "date_out": {"type": "string", "format": "date-time"}
      }
    },
    "ServiceTicketCreate": {
      "type": "object",
      "required": ["description"],
      "properties": {
        "vin": {"type": "string", "description": "Vehicle VIN (preferred)"},
        "vehicle_id": {"type": "integer", "description": "Optional alternative; server will resolve VIN"},
        "description": {"type": "string"},
        "status": {"type": "string", "enum": ["open", "in_progress", "closed"]}
      }
    },
    "ServiceTicketUpdate": {
      "type": "object",
      "properties": {
        "description": {"type": "string"},
        "status": {"type": "string", "enum": ["open", "in_progress", "closed"]},
        "add_ids": {"type": "array", "items": {"type": "integer"}, "description": "Mechanic IDs to add"},
        "remove_ids": {"type": "array", "items": {"type": "integer"}, "description": "Mechanic IDs to remove"}
      }
    },

    "TicketAssignmentUpdate": {
      "type": "object",
      "properties": {
        "mechanic_ids": {"type": "array", "items": {"type": "integer"}},
        "inventory_ids": {"type": "array", "items": {"type": "integer"}}
      }
    }
  }
}
