"""
Curated job role templates.

Users pick a role and get a realistic, editable job description pre-filled in
the form instead of typing one from scratch. Descriptions are written in the
format the job parser understands best: explicit "Required skills:" /
"Preferred:" sections, an "N+ years" experience sentence, and bullet
responsibilities.
"""
from __future__ import annotations

from app.schemas import ExperienceLevel

# (id, title, category, experience_level, description)
_TEMPLATES: list[dict] = [
    {
        "id": "senior-backend-engineer",
        "title": "Senior Backend Engineer",
        "category": "Engineering",
        "experience_level": ExperienceLevel.SENIOR,
        "description": (
            "We are looking for a Senior Backend Engineer with 5+ years of experience "
            "to design and scale our core services.\n\n"
            "Required skills: Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, "
            "REST API, microservices.\n"
            "Preferred: Terraform, Redis, GraphQL, Kafka.\n\n"
            "Responsibilities:\n"
            "• Design and build scalable backend systems and REST APIs\n"
            "• Lead architecture decisions and code reviews\n"
            "• Optimise database queries and service performance\n"
            "• Collaborate with cross-functional teams in an Agile environment\n"
            "• Mentor junior engineers"
        ),
    },
    {
        "id": "frontend-engineer",
        "title": "Frontend Engineer",
        "category": "Engineering",
        "experience_level": ExperienceLevel.MID,
        "description": (
            "We are looking for a Frontend Engineer with 3+ years of experience to craft "
            "fast, accessible user interfaces.\n\n"
            "Required skills: JavaScript, TypeScript, React, HTML, CSS, REST API, Git.\n"
            "Preferred: Next.js, Tailwind CSS, GraphQL, Jest, Cypress.\n\n"
            "Responsibilities:\n"
            "• Build responsive, accessible UI components in React\n"
            "• Integrate frontend features with REST and GraphQL APIs\n"
            "• Optimise bundle size and core web vitals\n"
            "• Write unit and end-to-end tests for critical flows\n"
            "• Participate in design reviews with UX designers"
        ),
    },
    {
        "id": "fullstack-engineer",
        "title": "Full-Stack Engineer",
        "category": "Engineering",
        "experience_level": ExperienceLevel.MID,
        "description": (
            "We are looking for a Full-Stack Engineer with 3+ years of experience to own "
            "features end to end, from database schema to pixel-perfect UI.\n\n"
            "Required skills: TypeScript, React, Node.js, PostgreSQL, Docker, REST API, Git.\n"
            "Preferred: AWS, GraphQL, Redis, CI/CD, Prisma.\n\n"
            "Responsibilities:\n"
            "• Develop user-facing features with React and TypeScript\n"
            "• Build and maintain Node.js services and PostgreSQL schemas\n"
            "• Ship features through automated CI/CD pipelines\n"
            "• Debug production issues across the full stack\n"
            "• Contribute to technical design discussions"
        ),
    },
    {
        "id": "devops-sre-engineer",
        "title": "DevOps / SRE Engineer",
        "category": "Infrastructure",
        "experience_level": ExperienceLevel.SENIOR,
        "description": (
            "We are looking for a DevOps / SRE Engineer with 5+ years of experience to keep "
            "our platform reliable, observable, and fast to deploy.\n\n"
            "Required skills: Docker, Kubernetes, Terraform, AWS, CI/CD, Linux, Python, "
            "Git, monitoring.\n"
            "Preferred: Prometheus, Grafana, Ansible, Helm, Go.\n\n"
            "Responsibilities:\n"
            "• Build and maintain Kubernetes clusters and Terraform infrastructure\n"
            "• Automate CI/CD pipelines and deployment strategies\n"
            "• Define SLOs, alerting, and dashboards for production systems\n"
            "• Lead incident response and blameless post-mortems\n"
            "• Reduce cloud costs through right-sizing and automation"
        ),
    },
    {
        "id": "data-scientist",
        "title": "Data Scientist",
        "category": "Data & AI",
        "experience_level": ExperienceLevel.MID,
        "description": (
            "We are looking for a Data Scientist with 3+ years of experience to turn data "
            "into products and decisions.\n\n"
            "Required skills: Python, SQL, Machine Learning, Pandas, scikit-learn, "
            "statistics, data visualisation.\n"
            "Preferred: Deep Learning, PyTorch, NLP, Spark, Tableau, A/B testing.\n\n"
            "Responsibilities:\n"
            "• Build and deploy machine learning models for business problems\n"
            "• Analyse large datasets to surface actionable insights\n"
            "• Design and evaluate A/B tests and experiments\n"
            "• Communicate findings to product and engineering stakeholders\n"
            "• Maintain reproducible data science pipelines"
        ),
    },
    {
        "id": "ml-engineer",
        "title": "Machine Learning Engineer",
        "category": "Data & AI",
        "experience_level": ExperienceLevel.SENIOR,
        "description": (
            "We are looking for a Machine Learning Engineer with 5+ years of experience to "
            "productionise ML systems at scale.\n\n"
            "Required skills: Python, Machine Learning, PyTorch, TensorFlow, Docker, "
            "Kubernetes, AWS, SQL, MLOps.\n"
            "Preferred: NLP, LLMs, MLflow, Airflow, Spark, CUDA.\n\n"
            "Responsibilities:\n"
            "• Take models from research notebooks to production APIs\n"
            "• Build training, evaluation, and monitoring pipelines\n"
            "• Optimise inference latency and GPU utilisation\n"
            "• Partner with data scientists on feature engineering\n"
            "• Establish MLOps best practices across the team"
        ),
    },
    {
        "id": "data-engineer",
        "title": "Data Engineer",
        "category": "Data & AI",
        "experience_level": ExperienceLevel.MID,
        "description": (
            "We are looking for a Data Engineer with 3+ years of experience to build the "
            "pipelines that power our analytics and ML.\n\n"
            "Required skills: Python, SQL, Apache Spark, Airflow, PostgreSQL, Docker, "
            "ETL, data warehousing.\n"
            "Preferred: Kafka, dbt, Snowflake, AWS Glue, Redshift, Databricks.\n\n"
            "Responsibilities:\n"
            "• Design and operate batch and streaming data pipelines\n"
            "• Model warehouse schemas for analytics workloads\n"
            "• Ensure data quality with automated checks and lineage\n"
            "• Optimise pipeline cost and runtime\n"
            "• Enable self-service analytics for downstream teams"
        ),
    },
    {
        "id": "mobile-engineer",
        "title": "Mobile Engineer",
        "category": "Engineering",
        "experience_level": ExperienceLevel.MID,
        "description": (
            "We are looking for a Mobile Engineer with 3+ years of experience to build our "
            "cross-platform mobile apps.\n\n"
            "Required skills: React Native, TypeScript, JavaScript, REST API, Git, mobile "
            "UI design.\n"
            "Preferred: Flutter, Swift, Kotlin, Firebase, offline storage, push notifications.\n\n"
            "Responsibilities:\n"
            "• Ship features to iOS and Android from a shared codebase\n"
            "• Build smooth, native-feeling user interfaces\n"
            "• Integrate analytics, crash reporting, and push notifications\n"
            "• Manage app store releases and review processes\n"
            "• Improve app performance and startup time"
        ),
    },
    {
        "id": "qa-automation-engineer",
        "title": "QA / Test Automation Engineer",
        "category": "Engineering",
        "experience_level": ExperienceLevel.MID,
        "description": (
            "We are looking for a QA / Test Automation Engineer with 3+ years of experience "
            "to raise the quality bar across our web products.\n\n"
            "Required skills: Python or JavaScript, Selenium, Cypress, REST API testing, "
            "Git, CI/CD, SQL.\n"
            "Preferred: Playwright, pytest, k6, TestNG, Jira, performance testing.\n\n"
            "Responsibilities:\n"
            "• Design and maintain automated regression test suites\n"
            "• Integrate tests into CI/CD pipelines with clear reporting\n"
            "• Perform API, UI, and exploratory testing\n"
            "• Track defects end to end and verify fixes\n"
            "• Champion shift-left quality practices with developers"
        ),
    },
    {
        "id": "product-manager",
        "title": "Product Manager",
        "category": "Product & Design",
        "experience_level": ExperienceLevel.MID,
        "description": (
            "We are looking for a Product Manager with 3+ years of experience to own the "
            "roadmap for our SaaS platform.\n\n"
            "Required skills: product strategy, roadmap planning, user research, agile, "
            "stakeholder management, data analysis, SQL.\n"
            "Preferred: A/B testing, Figma, Jira, B2B SaaS, growth analytics.\n\n"
            "Responsibilities:\n"
            "• Define product vision, roadmap, and success metrics\n"
            "• Gather requirements through user interviews and data\n"
            "• Write clear specs and prioritise the backlog with engineering\n"
            "• Run experiments and iterate based on evidence\n"
            "• Align stakeholders across design, engineering, and go-to-market"
        ),
    },
    {
        "id": "ux-ui-designer",
        "title": "UX/UI Designer",
        "category": "Product & Design",
        "experience_level": ExperienceLevel.MID,
        "description": (
            "We are looking for a UX/UI Designer with 3+ years of experience to shape "
            "intuitive product experiences.\n\n"
            "Required skills: Figma, user research, wireframing, prototyping, design "
            "systems, usability testing, interaction design.\n"
            "Preferred: accessibility (WCAG), motion design, HTML, CSS, design tokens.\n\n"
            "Responsibilities:\n"
            "• Design flows, wireframes, and high-fidelity mockups in Figma\n"
            "• Maintain and evolve our component-based design system\n"
            "• Run usability tests and synthesise findings\n"
            "• Partner with engineers to ensure design fidelity\n"
            "• Advocate for accessibility and inclusive design"
        ),
    },
    {
        "id": "security-engineer",
        "title": "Security Engineer",
        "category": "Infrastructure",
        "experience_level": ExperienceLevel.SENIOR,
        "description": (
            "We are looking for a Security Engineer with 5+ years of experience to protect "
            "our platform and customer data.\n\n"
            "Required skills: application security, penetration testing, OWASP, Linux, "
            "Python, cloud security (AWS), incident response.\n"
            "Preferred: Kubernetes security, SIEM, threat modelling, SOC 2, Burp Suite.\n\n"
            "Responsibilities:\n"
            "• Run security reviews, pen tests, and vulnerability management\n"
            "• Harden cloud infrastructure and container workloads\n"
            "• Build detection and response capabilities\n"
            "• Lead security incident response and lessons learned\n"
            "• Train engineers on secure coding practices"
        ),
    },
    {
        "id": "cloud-architect",
        "title": "Cloud Solutions Architect",
        "category": "Infrastructure",
        "experience_level": ExperienceLevel.LEAD,
        "description": (
            "We are looking for a Cloud Solutions Architect with 7+ years of experience to "
            "design our next-generation cloud platform.\n\n"
            "Required skills: AWS, Terraform, Kubernetes, networking, security, "
            "microservices, cost optimisation, Python or Go.\n"
            "Preferred: Azure or GCP multi-cloud, Well-Architected reviews, IAM, VPC design.\n\n"
            "Responsibilities:\n"
            "• Design scalable, secure, cost-aware cloud architectures\n"
            "• Set infrastructure standards and reference implementations\n"
            "• Guide migration of legacy workloads to the cloud\n"
            "• Review designs for reliability and security\n"
            "• Mentor engineers on cloud best practices"
        ),
    },
    {
        "id": "business-analyst",
        "title": "Business Analyst",
        "category": "Product & Design",
        "experience_level": ExperienceLevel.MID,
        "description": (
            "We are looking for a Business Analyst with 3+ years of experience to bridge "
            "business needs and technical delivery.\n\n"
            "Required skills: requirements gathering, SQL, data analysis, process mapping, "
            "stakeholder management, Excel, documentation.\n"
            "Preferred: Power BI, Tableau, Jira, agile ceremonies, domain modelling.\n\n"
            "Responsibilities:\n"
            "• Elicit and document business and functional requirements\n"
            "• Analyse data to support decisions and measure impact\n"
            "• Map current and future-state business processes\n"
            "• Coordinate UAT and rollout plans with stakeholders\n"
            "• Translate feedback into actionable backlog items"
        ),
    },
    {
        "id": "software-engineer-intern",
        "title": "Software Engineer (Intern)",
        "category": "Engineering",
        "experience_level": ExperienceLevel.INTERN,
        "description": (
            "We are looking for a motivated Software Engineering Intern to join our product "
            "team. No professional experience required — strong fundamentals matter most.\n\n"
            "Required skills: Python or JavaScript, data structures, algorithms, Git, "
            "SQL basics, eagerness to learn.\n"
            "Preferred: React, FastAPI or Node.js, personal projects, hackathon experience.\n\n"
            "Responsibilities:\n"
            "• Implement small features with guidance from a mentor\n"
            "• Write tests and documentation for your code\n"
            "• Participate in stand-ups, code reviews, and sprint planning\n"
            "• Fix bugs and improve tooling across the stack"
        ),
    },
]

# Public shape — validated at import time so a bad edit fails loudly in tests.
TEMPLATES: list[dict] = sorted(_TEMPLATES, key=lambda t: (t["category"], t["title"]))
