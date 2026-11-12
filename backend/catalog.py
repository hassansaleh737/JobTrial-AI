"""Self-contained, human-reviewed challenge fixtures and mission definitions."""
TRACKS = {
    "backend": {
        "title": "Backend Engineer", "subtitle": "Debug production-like Python logic",
        "category": "Engineering", "duration": "20–30 min", "difficulty": "Junior",
        "color": "#5865e9", "skills": ["Python", "API Logic", "Debugging", "Edge Cases"],
        "intro": "Your simulated engineering lead needs an urgent fix before an order service release. Fix the function, run the test suite, and ship a working result.",
        "company": "Northstar Commerce", "role": "Junior Backend Engineer",
        "keywords": ["python", "fastapi", "backend", "back-end", "api", "django", "flask", "rest"],
        "tasks": [
            {"id":"order-total","title":"Fix the order total bug","tag":"Bug fix · Python","time":"12 min","goal":"Calculate the final price after a percentage discount. Return the total rounded to 2 decimal places.",
             "spec":["total = unit_price × quantity × (1 − discount_pct / 100)","The discount is a percentage, not a fixed amount.","Keep the function name and parameter list unchanged."],
             "starter":"def calculate_total(unit_price, quantity, discount_pct):\n    return round(unit_price * quantity - discount_pct, 2)",
             "hint":"10% off 100 × 2 should be 180, not 190.","lang":"python"},
            {"id":"stock-guard","title":"Prevent overselling inventory","tag":"Business logic · Python","time":"10 min","goal":"Return the remaining stock, but return -1 if the customer requests more items than are available.",
             "spec":["If requested > current_stock, return -1.","Otherwise return current_stock − requested.","Your function must handle zero and exact-quantity requests."],
             "starter":"def remaining_stock(current_stock, requested):\n    return current_stock - requested",
             "hint":"Use a conditional expression: value_if_true if condition else value_if_false.","lang":"python"},
        ],
    },
    "sql": {
        "title":"Data Analyst", "subtitle":"Investigate commerce data using real SQL",
        "category":"Analytics", "duration":"20–30 min", "difficulty":"Junior",
        "color":"#11947f", "skills":["SQL", "Data Analysis", "Aggregation", "Joins"],
        "intro":"The operations team needs numbers it can trust. Work with an actual SQLite database and submit queries that pass hidden data checks.",
        "company":"Meridian Retail", "role":"Junior Data Analyst",
        "keywords":["sql", "data analyst", "analytics", "business intelligence", "power bi", "data analysis", "data scientist", "reporting"],
        "tasks":[
            {"id":"revenue","title":"Calculate paid revenue by region","tag":"SQL · Aggregations","time":"12 min","goal":"Report total paid sales revenue per region, highest first.",
             "spec":["Use the orders table.","Only orders with status = 'paid' count.","Revenue is quantity × unit_price, not the number of orders.","Return exactly two columns: region and revenue."],
             "starter":"SELECT region, SUM(unit_price) AS revenue\nFROM orders\nGROUP BY region\nORDER BY revenue DESC;",
             "hint":"Filter paid orders and multiply unit_price by quantity before summing.","lang":"sql"},
            {"id":"repeat-buyers","title":"Find your repeat customers","tag":"SQL · Joins","time":"12 min","goal":"Return the names and paid-order counts of customers who placed at least 2 paid orders.",
             "spec":["Join orders to customers on customer_id.","Only paid orders count.","Return customer_name and order_count.","Sort by order_count descending, then customer_name ascending."],
             "starter":"SELECT c.name AS customer_name, COUNT(*) AS order_count\nFROM customers c\nJOIN orders o ON o.customer_id = c.id\nGROUP BY c.id;",
             "hint":"WHERE o.status = 'paid' and HAVING COUNT(*) >= 2 are key.","lang":"sql"},
        ],
    },
    "frontend": {
        "title":"Frontend Developer", "subtitle":"Ship an accessible responsive signup page",
        "category":"Engineering", "duration":"15–25 min", "difficulty":"Junior",
        "color":"#c07732", "skills":["HTML", "CSS", "Accessibility", "Responsive Design"],
        "intro":"A product designer sent a broken signup page. Implement a usable, accessible interface. Preview your code and run the quality checks.",
        "company":"Lumen Studio", "role":"Junior Frontend Engineer",
        "keywords":["frontend", "front-end", "react", "html", "css", "javascript", "web developer", "ui developer", "web design"],
        "tasks":[
            {"id":"signup","title":"Repair the signup experience","tag":"HTML + CSS · UI","time":"20 min","goal":"Build a clear, responsive signup form with accessible labeling and visible keyboard focus.",
             "spec":["Include a main heading and an email input.","Associate a visible label with the email input.","Add a submit button inside the form.","Use a media query for smaller screens and visible :focus styles."],
             "starter_html":"<main class=\"page\">\n  <section class=\"card\">\n    <h1>Join Lumen</h1>\n    <p>Better work starts here.</p>\n    <form>\n      <input type=\"email\" placeholder=\"Your email\">\n    </form>\n  </section>\n</main>",
             "starter_css":"* { box-sizing: border-box; }\nbody { margin: 0; font-family: system-ui, sans-serif; background: #f2f5fa; }\n.page { min-height: 100vh; display: grid; place-items: center; padding: 24px; }\n.card { background: white; padding: 40px; width: 480px; border-radius: 20px; }\nh1 { font-size: 32px; }",
             "hint":"Add a <label for=\"email\"> and <input id=\"email\">, a submit button, @media, and :focus-visible.","lang":"html"},
        ],
    },
    "security": {
        "title":"Security Analyst", "subtitle":"Investigate suspicious authentication logs",
        "category":"Security", "duration":"15–20 min", "difficulty":"Junior",
        "color":"#a8629b", "skills":["Log Analysis", "Incident Triage", "Evidence", "Response"],
        "intro":"The SOC has flagged a surge in failed logins. Review the evidence, identify the source, and send a brief incident assessment.",
        "company":"Atlas Security Ops", "role":"SOC Analyst Intern",
        "keywords":["security", "cybersecurity", "soc analyst", "siem", "incident", "threat", "blue team", "log analysis", "network security"],
        "tasks":[
            {"id":"auth-triage","title":"Triage the suspicious sign-in activity","tag":"SOC · Investigation","time":"15 min","goal":"Identify the suspicious IP, classify the activity, choose supporting logs, and recommend a response.",
             "spec":["Analyze the provided fictional authentication logs.","Identify a probable attack based on the full sequence, not a single 401.","Select at least three supporting log events.","Write a concise incident note and choose a response action."],
             "hint":"Look for a cluster of unsuccessful logins across usernames followed by a success.","lang":"investigation"},
        ],
    },
}

DEMO_JOBS = [
    {"id":"backend","title":"Junior Python Backend Developer","company":"Northstar Commerce","description":"We are looking for a Junior Backend Developer with Python, FastAPI, REST API development, debugging, testing, and basic business logic skills. Help maintain our orders service."},
    {"id":"sql","title":"Data Analyst Intern","company":"Meridian Retail","description":"Seeking a Data Analyst intern to investigate business performance. Required skills include SQL, data analysis, aggregation, joins, and reporting."},
    {"id":"frontend","title":"Frontend Developer Intern","company":"Lumen Studio","description":"Frontend developer intern wanted. You should know HTML, CSS, JavaScript, responsive web design, and accessibility standards."},
    {"id":"security","title":"SOC Analyst Intern","company":"Atlas Security Ops","description":"Cybersecurity SOC analyst internship: log analysis, incident response, SIEM, authentication monitoring, and threat investigation."},
]

ORDERS = [
    (1,1,'Cairo',2,120.0,'paid'), (2,2,'Giza',1,340.0,'paid'),
    (3,1,'Cairo',3,60.0,'paid'), (4,3,'Alexandria',1,450.0,'refunded'),
    (5,2,'Giza',2,150.0,'paid'), (6,3,'Alexandria',4,75.0,'paid'),
    (7,4,'Cairo',1,250.0,'pending'), (8,4,'Cairo',1,95.0,'paid'),
    (9,1,'Cairo',1,180.0,'paid'), (10,2,'Giza',1,80.0,'refunded'),
]
CUSTOMERS = [(1,'Nour'),(2,'Kareem'),(3,'Lina'),(4,'Omar')]

SECURITY_LOGS = [
    {"id":1,"time":"09:40:11","ip":"192.0.2.51","user":"nour","event":"LOGIN_SUCCESS","status":200,"path":"/auth/login"},
    {"id":2,"time":"09:40:39","ip":"198.51.100.25","user":"kareem","event":"LOGIN_SUCCESS","status":200,"path":"/auth/login"},
    {"id":3,"time":"09:41:07","ip":"203.0.113.44","user":"admin","event":"LOGIN_FAILED","status":401,"path":"/auth/login"},
    {"id":4,"time":"09:41:09","ip":"203.0.113.44","user":"nour","event":"LOGIN_FAILED","status":401,"path":"/auth/login"},
    {"id":5,"time":"09:41:10","ip":"203.0.113.44","user":"kareem","event":"LOGIN_FAILED","status":401,"path":"/auth/login"},
    {"id":6,"time":"09:41:12","ip":"203.0.113.44","user":"lina","event":"LOGIN_FAILED","status":401,"path":"/auth/login"},
    {"id":7,"time":"09:41:15","ip":"203.0.113.44","user":"nour","event":"LOGIN_SUCCESS","status":200,"path":"/auth/login"},
    {"id":8,"time":"09:41:45","ip":"192.0.2.51","user":"nour","event":"PAGE_VIEW","status":200,"path":"/dashboard"},
    {"id":9,"time":"09:42:02","ip":"198.51.100.25","user":"kareem","event":"LOGOUT","status":200,"path":"/auth/logout"},
    {"id":10,"time":"09:42:18","ip":"198.51.100.80","user":"lina","event":"LOGIN_FAILED","status":401,"path":"/auth/login"},
    {"id":11,"time":"09:42:25","ip":"198.51.100.80","user":"lina","event":"LOGIN_SUCCESS","status":200,"path":"/auth/login"},
]
