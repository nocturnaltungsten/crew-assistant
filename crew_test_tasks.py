#!/usr/bin/env python3
"""
Extended Task Bank for Crew Workflow Testing
Comprehensive collection of tasks across all complexity levels
"""

# Extended task examples for more comprehensive testing
EXTENDED_TASK_BANK = {
    "trivial": [
        "What is Python?",
        "List 5 programming languages",
        "Explain what a variable is",
        "Define REST API",
        "What is Git?",
        "What is a database?",
        "Explain HTML basics",
        "What is CSS?",
        "Define machine learning",
        "What is cloud computing?",
        "Explain what JSON is",
        "What is an API?",
        "Define version control",
        "What is a framework?",
        "Explain debugging",
        "What is a compiler?",
        "Define agile methodology",
        "What is DevOps?",
        "Explain open source",
        "What is encryption?",
    ],
    
    "simple": [
        "Write a Python function to calculate factorial",
        "Create a simple HTML contact form",
        "Write a bash script to backup files",
        "Create a basic calculator in Python",
        "Write SQL to find top 5 customers",
        "Create a simple password generator",
        "Write a function to reverse a string",
        "Create a basic sorting algorithm",
        "Write a script to read CSV files",
        "Create a simple unit converter",
        "Write a function to validate email addresses",
        "Create a basic todo list in HTML/CSS",
        "Write a Python script to rename files",
        "Create a simple random quote generator",
        "Write a function to find prime numbers",
        "Create a basic word counter",
        "Write a script to download files",
        "Create a simple temperature converter",
        "Write a function to generate QR codes",
        "Create a basic time tracker",
    ],
    
    "moderate": [
        "Build a REST API for a todo app with authentication",
        "Create a web scraper that saves data to CSV",
        "Build a chat application using WebSockets",
        "Design a database schema for an e-commerce site",
        "Create a CI/CD pipeline for a Python project",
        "Build a blog platform with user accounts",
        "Create a file upload service with virus scanning",
        "Build a URL shortener with analytics",
        "Create a weather dashboard with API integration",
        "Build a password manager with encryption",
        "Create a expense tracker with categories",
        "Build a inventory management system",
        "Create a booking system for appointments",
        "Build a social media feed aggregator",
        "Create a code snippet manager",
        "Build a survey creation platform",
        "Create a project time tracking system",
        "Build a customer support ticket system",
        "Create a document collaboration tool",
        "Build a event management platform",
    ],
    
    "complex": [
        "Build a microservices architecture for user management with Docker",
        "Create a real-time analytics dashboard with React and Python backend",
        "Design and implement a distributed caching system",
        "Build a machine learning pipeline for text classification",
        "Create a full-stack e-commerce platform with payment integration",
        "Build a video streaming platform with CDN integration",
        "Create a cryptocurrency trading bot with ML predictions",
        "Build a collaborative code editor with real-time sync",
        "Create a container orchestration system with auto-scaling",
        "Build a distributed database with replication",
        "Create a real-time fraud detection system",
        "Build a social media platform with ML content recommendation",
        "Create a IoT device management platform",
        "Build a serverless data processing pipeline",
        "Create a multi-tenant SaaS platform architecture",
        "Build a distributed search engine",
        "Create a blockchain-based voting system",
        "Build a real-time collaborative whiteboard",
        "Create a AI-powered customer service platform",
        "Build a distributed file storage system",
    ],
    
    "vague": [
        "Make something cool",
        "Build an app",
        "Create a system for managing stuff",
        "I need something automated",
        "Build a game",
        "Make it better",
        "Fix this problem",
        "Optimize performance",
        "Create something useful",
        "Build a tool",
        "Make it work",
        "Improve the process",
        "Create a solution",
        "Build something modern",
        "Make it faster",
        "Create something innovative",
        "Build a platform",
        "Make it user-friendly",
        "Create something scalable",
        "Build something secure",
    ],
    
    "vague_override": [
        "Make something cool - JUST BUILD IT",
        "Build an app. Do your best with what I've given you",
        "Create a system for managing stuff. Just build it the best you can",
        "I need something automated - work with what I've told you",
        "Build a game - JUST BUILD IT",
        "Make it better - proceed anyway",
        "Fix this problem - just build something that works",
        "Optimize performance - do the best you can",
        "Create something useful - JUST BUILD IT",
        "Build a tool - work with what I've told you",
        "Make it work - just build it the best you can",
        "Improve the process - proceed anyway",
        "Create a solution - JUST BUILD IT",
        "Build something modern - do your best",
        "Make it faster - work with what I've given you",
        "Create something innovative - JUST BUILD IT",
        "Build a platform - just build something",
        "Make it user-friendly - proceed anyway",
        "Create something scalable - do the best you can",
        "Build something secure - JUST BUILD IT",
        # Test override on simple tasks that normally get rejected
        "Create a sorting algorithm - JUST BUILD IT",
        "Build a password manager - do the best you can",
        "Create a word counter - work with what I've given you",
        "Write a calculator - JUST BUILD IT",
        "Build a web scraper - proceed anyway",
        "Create a todo app - just build it",
        "Write a file organizer - do your best",
        "Build a chat bot - JUST BUILD IT",
    ],
    
    # Additional specialized categories for testing specific aspects
    "validation_testing": [
        # These should trigger clarification requests
        "Build me something",
        "Create an application",
        "Make a website",
        "I want software",
        "Design something good",
        
        # These should be approved with JUST BUILD IT
        "Build me something - JUST BUILD IT",
        "Create an application - do your best",
        "Make a website - work with what I've got",
        "I want software - just build it",
        "Design something good - proceed anyway",
    ],
    
    "agent_stress_testing": [
        # Tasks designed to test specific agents
        "Analyze the user experience requirements for a mobile banking app", # UX heavy
        "Create a detailed 6-month development roadmap for a startup", # Planner heavy  
        "Implement a complete REST API with all CRUD operations", # Developer heavy
        "Review and validate this complex system architecture proposal", # Reviewer heavy
    ],
    
    "workflow_edge_cases": [
        # Edge cases for workflow testing
        "Build a Pong game with cute animations and fun sounds",
        "Create a web scraper but make it respectful and ethical",
        "Build a password manager that's both secure and user-friendly",
        "Create a chat bot that's helpful but not creepy",
        "Build a todo app that actually helps with productivity",
    ]
}

# Weights for extended testing (can be used to override defaults)
EXTENDED_WEIGHTS = {
    "trivial": 3.0,
    "simple": 3.0, 
    "moderate": 2.5,
    "complex": 2.0,
    "vague": 1.5,
    "vague_override": 2.0,
    "validation_testing": 1.0,
    "agent_stress_testing": 1.0,
    "workflow_edge_cases": 1.5,
}

def get_task_bank():
    """Get the extended task bank."""
    return EXTENDED_TASK_BANK

def get_weights():
    """Get the extended weights."""
    return EXTENDED_WEIGHTS

def get_random_task(category: str) -> str:
    """Get a random task from a specific category."""
    import random
    if category in EXTENDED_TASK_BANK:
        return random.choice(EXTENDED_TASK_BANK[category])
    else:
        raise ValueError(f"Unknown category: {category}")

def get_all_categories():
    """Get all available task categories."""
    return list(EXTENDED_TASK_BANK.keys())

if __name__ == "__main__":
    # Print task bank statistics
    print("🧪 Extended Crew Test Task Bank")
    print("=" * 40)
    
    total_tasks = 0
    for category, tasks in EXTENDED_TASK_BANK.items():
        count = len(tasks)
        total_tasks += count
        weight = EXTENDED_WEIGHTS.get(category, 1.0)
        print(f"{category:20} | {count:3d} tasks | weight {weight}")
    
    print("=" * 40)
    print(f"Total tasks: {total_tasks}")
    
    # Show a few random examples
    print("\n🎲 Random task examples:")
    import random
    for category in ["trivial", "simple", "moderate", "complex", "vague", "vague_override"]:
        example = get_random_task(category)
        print(f"{category:15} | {example}")