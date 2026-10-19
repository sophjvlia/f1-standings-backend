# F1 Driver's Championship API 🏎️⚡

A high-performance, serverless REST API built with **AWS Lambda**, **API Gateway**, and **AWS ElastiCache (Valkey)** using **Python 3.11**. The service dynamically fetches and processes Formula 1 standings from the OpenF1 API, formatting leaderboard data and caching results to maintain fast response times and avoid external API rate limits.

---

## 🌟 Key Features

* **Serverless Architecture**: Built using AWS SAM (Serverless Application Model) with auto-scaling API Gateway and Lambda functions.
* **ElastiCache Caching**: Integrates with ElastiCache (Valkey) over TLS in a private VPC. Historical seasons are cached permanently, while active seasons utilize an expiring TTL cache.
* **Dynamic Year Querying**: Supports driver standings for any F1 season from 2023 onwards (e.g., `?year=2024`), defaulting to the current season (`2026`).
* **OpenF1 Data Aggregation**: Resolves session keys, merges driver biographical details with raw points standings, and builds a clean JSON payload.
* **CI/CD Pipeline**: Fully automated build and deployment via GitHub Actions (`sam deploy`).

---

## 🏗️ Architecture Overview

```
[ Client Request ] 
       │
       ▼
[ API Gateway ]
       │
       ▼
[ AWS Lambda (In VPC) ]
       ├─── (1. Check Cache) ────► [ ElastiCache / Valkey (TLS) ]
       │                                     │
       │ (Cache Hit - Return JSON) ◄─────────┘
       │
       └─── (2. Cache Miss) ─────► [ OpenF1 API (v1) ]
                                             │
         (Merge & Store) ◄───────────────────┘
```

---

## 🚀 API Documentation

### **Endpoint**
`GET /drivers_championship`

### **Query Parameters**
| Parameter | Type   | Required | Default | Description |
| :---      | :---   | :---     | :---    | :--- |
| `year`    | String | No       | `2026`  | F1 Season year (Supported: `2023` to present). |

---

### **Example Requests & Responses**

#### 1. Fetch Default Season (2026)
```bash
curl -X GET "https://<your-api-id>.execute-api.us-east-1.amazonaws.com/Prod/drivers_championship"
```

#### 2. Fetch Historical Season (2024)
```bash
curl -X GET "https://<your-api-id>.execute-api.us-east-1.amazonaws.com/Prod/drivers_championship?year=2024"
```

**Success Response (`200 OK`):**
```json
[
  {
    "position": 1,
    "points": 429.0,
    "driver_number": 1,
    "full_name": "Max VERSTAPPEN",
    "name_acronym": "VER",
    "team_name": "Red Bull Racing",
    "team_colour": "3671C6",
    "headshot_url": "https://www.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png"
  },
  {
    "position": 2,
    "points": 341.0,
    "driver_number": 4,
    "full_name": "Lando NORRIS",
    "name_acronym": "NOR",
    "team_name": "McLaren",
    "team_colour": "FF8000",
    "headshot_url": "https://www.formula1.com/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png"
  }
]
```

#### 3. Request Unsupported Year (`< 2023`)
```bash
curl -X GET "https://<your-api-id>.execute-api.us-east-1.amazonaws.com/Prod/drivers_championship?year=2021"
```

**Error Response (`400 Bad Request`):**
```json
{
  "error": "Data for year 2021 is not available. OpenF1 only supports data from 2023 onwards."
}
```

---

## 🛠️ Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── deploy.yml            # CI/CD deployment pipeline via GitHub Actions
├── src/
│   └── drivers_championship.py   # Lambda entrypoint & core handler logic
├── template.yaml                 # AWS SAM infrastructure definition
├── requirements.txt              # Python dependencies (redis, requests, etc.)
└── README.md                     # Project documentation
```

---

## 💻 Local Setup & Deployment

### **Prerequisites**
* [AWS CLI](https://aws.amazon.com/cli/) configured with credentials.
* [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed.
* Python 3.11+.

### **Deployment via SAM**
1. **Build application artifacts:**
   ```bash
   sam build
   ```

2. **Deploy to AWS:**
   ```bash
   sam deploy --guided
   ```
   *Provide the `RedisHost`, `VpcSubnetIds`, and `LambdaSecurityGroupId` when prompted.*

### **Environment Variables**
The Lambda function relies on the following environment variables (configured via `template.yaml`):

| Variable | Description |
| :--- | :--- |
| `REDIS_HOST` | Endpoint domain for your ElastiCache cluster. |
| `REDIS_PORT` | Port for ElastiCache (default: `6379`). |

---

## 🔒 Security & Networking

* **VPC Isolation**: The Lambda function operates inside private subnets connected to your target VPC.
* **TLS Encryption**: All cache connections enforce SSL/TLS (`ssl=True`) required by ElastiCache Serverless.
* **Security Groups**: Inbound access to port `6379` on ElastiCache is strictly restricted to the assigned Lambda Security Group.