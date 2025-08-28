# app/swagger.py
swagger_spec = {
  "swagger": "2.0",
  "info": {
    "title": "Mechanic Shop API",
    "version": "1.0.0",
    "description": "CRUD for customers, mechanics, inventory, service tickets + auth, rate-limits, and caching."
  },
  "basePath": "/",  # adjust if you prefix
  "schemes": ["http", "https"],
  "consumes": ["application/json"],
  "produces": ["application/json"],
  "securityDefinitions": {
    "BearerAuth": {
      "type": "apiKey",
      "name": "Authorization",
      "in": "header",
      "description": "Use: Bearer <JWT>"
    }
  },
  "tags": [
    {"name": "Auth", "description": "Login & tokens"},
    {"name": "Customers", "description": "Customer CRUD"},
    {"name": "Mechanics", "description": "Mechanic CRUD"},
    {"name": "ServiceTickets", "description": "Tickets & assignments"},
    {"name": "Inventory", "description": "Parts inventory & linking"}
  ],
  "paths": {
    "/login": {
      "post": {
        "tags": ["Auth"],
        "summary": "Login and obtain JWT",
        "description": "Validates customer credentials and returns a JWT.",
        "parameters": [
          {
            "in": "body",
            "name": "credentials",
            "schema": {"$ref": "#/definitions/LoginRequest"},
            "required": True
          }
        ],
        "responses": {
          "200": {
            "description": "Token issued",
            "schema": {"$ref": "#/definitions/AuthToken"},
            "examples": {"application/json": {"token": "<jwt>"}}
          },
          "401": {"description": "Invalid credentials", "schema": {"$ref": "#/definitions/Error"}}
        }
      }
    },

    "/customers/": {
      "get": {
        "tags": ["Customers"],
        "summary": "List customers",
        "description": "Returns a paginated list of customers (may be cached).",
        "responses": {
          "200": {
            "description": "OK",
            "schema": {
              "type": "array",
              "items": {"$ref": "#/definitions/Customer"}
            }
          }
        }
      },
      "post": {
        "tags": ["Customers"],
        "summary": "Create customer",
        "description": "Creates a new customer.",
        "parameters": [
          {
            "in": "body",
            "name": "payload",
            "schema": {"$ref": "#/definitions/CustomerCreate"},
            "required": True
          }
        ],
        "responses": {
          "201": {"description": "Created", "schema": {"$ref": "#/definitions/Customer"}},
          "400": {"description": "Validation error", "schema": {"$ref": "#/definitions/Error"}}
        }
      }
    },
    "/customers/{id}": {
      "get": {
        "tags": ["Customers"],
        "summary": "Get customer by id",
        "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}],
        "responses": {"200": {"schema": {"$ref": "#/definitions/Customer"}}, "404": {"$ref": "#/definitions/NotFound"}}
      },
      "put": {
        "tags": ["Customers"],
        "summary": "Update customer",
        "parameters": [
          {"name": "id", "in": "path", "required": True, "type": "integer"},
          {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/CustomerUpdate"}, "required": True}
        ],
        "responses": {"200": {"schema": {"$ref": "#/definitions/Customer"}}, "400": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}
      },
      "delete": {
        "tags": ["Customers"],
        "summary": "Delete customer",
        "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}],
        "responses": {"204": {"description": "Deleted"}, "404": {"$ref": "#/definitions/NotFound"}}
      }
    },

    "/mechanics/": {
      "get": {"tags": ["Mechanics"], "summary": "List mechanics", "responses": {"200": {"schema": {"type": "array", "items": {"$ref": "#/definitions/Mechanic"}}}}},
      "post": {
        "tags": ["Mechanics"], "summary": "Create mechanic",
        "parameters": [{"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/MechanicCreate"}, "required": True}],
        "responses": {"201": {"schema": {"$ref": "#/definitions/Mechanic"}}, "400": {"$ref": "#/definitions/Error"}}
      }
    },
    "/mechanics/{id}": {
      "get": {"tags": ["Mechanics"], "summary": "Get mechanic", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"200": {"schema": {"$ref": "#/definitions/Mechanic"}}, "404": {"$ref": "#/definitions/NotFound"}}},
      "put": {
        "tags": ["Mechanics"], "summary": "Update mechanic",
        "parameters": [
          {"name": "id", "in": "path", "required": True, "type": "integer"},
          {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/MechanicUpdate"}, "required": True}
        ],
        "responses": {"200": {"schema": {"$ref": "#/definitions/Mechanic"}}, "400": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}
      },
      "delete": {"tags": ["Mechanics"], "summary": "Delete mechanic", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"204": {"description": "Deleted"}, "404": {"$ref": "#/definitions/NotFound"}}}
    },

    "/inventory/": {
      "get": {"tags": ["Inventory"], "summary": "List parts (cached)", "responses": {"200": {"schema": {"type": "array", "items": {"$ref": "#/definitions/InventoryItem"}}}}},
      "post": {"tags": ["Inventory"], "summary": "Create part", "parameters": [{"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/InventoryCreate"}, "required": True}], "responses": {"201": {"schema": {"$ref": "#/definitions/InventoryItem"}}, "400": {"$ref": "#/definitions/Error"}}}
    },
    "/inventory/{id}": {
      "get": {"tags": ["Inventory"], "summary": "Get part", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"200": {"schema": {"$ref": "#/definitions/InventoryItem"}}, "404": {"$ref": "#/definitions/NotFound"}}},
      "put": {"tags": ["Inventory"], "summary": "Update part", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}, {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/InventoryUpdate"}, "required": True}], "responses": {"200": {"schema": {"$ref": "#/definitions/InventoryItem"}}, "400": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}},
      "delete": {"tags": ["Inventory"], "summary": "Delete part", "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"204": {"description": "Deleted"}, "404": {"$ref": "#/definitions/NotFound"}}}
    },

    "/service_tickets/": {
      "get": {
        "tags": ["ServiceTickets"],
        "summary": "List service tickets",
        "security": [{"BearerAuth": []}],
        "responses": {"200": {"schema": {"type": "array", "items": {"$ref": "#/definitions/ServiceTicket"}}}, "401": {"$ref": "#/definitions/Error"}}
      },
      "post": {
        "tags": ["ServiceTickets"],
        "summary": "Create ticket",
        "description": "Create a new service ticket (auth required).",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/ServiceTicketCreate"}, "required": True}],
        "responses": {"201": {"schema": {"$ref": "#/definitions/ServiceTicket"}}, "400": {"$ref": "#/definitions/Error"}, "401": {"$ref": "#/definitions/Error"}}
      }
    },
    "/service_tickets/{id}": {
      "get": {"tags": ["ServiceTickets"], "summary": "Get ticket", "security": [{"BearerAuth": []}], "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"200": {"schema": {"$ref": "#/definitions/ServiceTicket"}}, "401": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}},
      "put": {"tags": ["ServiceTickets"], "summary": "Update ticket", "security": [{"BearerAuth": []}], "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}, {"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/ServiceTicketUpdate"}, "required": True}], "responses": {"200": {"schema": {"$ref": "#/definitions/ServiceTicket"}}, "400": {"$ref": "#/definitions/Error"}, "401": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}},
      "delete": {"tags": ["ServiceTickets"], "summary": "Delete ticket", "security": [{"BearerAuth": []}], "parameters": [{"name": "id", "in": "path", "required": True, "type": "integer"}], "responses": {"204": {"description": "Deleted"}, "401": {"$ref": "#/definitions/Error"}, "404": {"$ref": "#/definitions/NotFound"}}}
    },

    "/service_tickets/{id}/assign": {
      "post": {
        "tags": ["ServiceTickets"],
        "summary": "Assign mechanics/parts to ticket",
        "security": [{"BearerAuth": []}],
        "parameters": [{"in": "body", "name": "payload", "schema": {"$ref": "#/definitions/TicketAssignmentUpdate"}, "required": True}, {"name": "id", "in": "path", "required": True, "type": "integer"}],
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
    "AuthToken": {
      "type": "object",
      "properties": {"token": {"type": "string"}}
    },

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
"CustomerCreate": {
  "type": "object",
  "required": ["first_name", "last_name", "address", "phone", "email", "password"],
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


    "Mechanic": {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}, "specialty": {"type": "string"}}},
    "MechanicCreate": {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}, "specialty": {"type": "string"}}},
    "MechanicUpdate": {"type": "object", "properties": {"name": {"type": "string"}, "specialty": {"type": "string"}}},

    "InventoryItem": {"type": "object", "properties": {"id": {"type": "integer"}, "sku": {"type": "string"}, "name": {"type": "string"}, "qty": {"type": "integer"}}},
    "InventoryCreate": {"type": "object", "required": ["sku", "name"], "properties": {"sku": {"type": "string"}, "name": {"type": "string"}, "qty": {"type": "integer", "default": 0}}},
    "InventoryUpdate": {"type": "object", "properties": {"sku": {"type": "string"}, "name": {"type": "string"}, "qty": {"type": "integer"}}},

    "ServiceTicket": {"type": "object", "properties": {"id": {"type": "integer"}, "vehicle_id": {"type": "integer"}, "customer_id": {"type": "integer"}, "status": {"type": "string"}}},
    "ServiceTicketCreate": {"type": "object", "required": ["vehicle_id", "customer_id"], "properties": {"vehicle_id": {"type": "integer"}, "customer_id": {"type": "integer"}, "notes": {"type": "string"}}},
    "ServiceTicketUpdate": {"type": "object", "properties": {"status": {"type": "string"}, "notes": {"type": "string"}}},

    "TicketAssignmentUpdate": {
      "type": "object",
      "properties": {
        "mechanic_ids": {"type": "array", "items": {"type": "integer"}},
        "inventory_ids": {"type": "array", "items": {"type": "integer"}}
      }
    }
  }
}
