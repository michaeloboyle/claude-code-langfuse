#!/usr/bin/env python3
"""
Basic Tracking Example - Simple Claude Code interaction logging
"""

from claude_logger import ClaudeCodeLogger

# Example 1: Using context manager (recommended)
def example_with_context_manager():
    """Track a Claude Code session using context manager"""

    with ClaudeCodeLogger(user_id="developer@example.com") as logger:

        # Log first interaction
        logger.log_interaction(
            user_prompt="Help me write a Python function to calculate fibonacci numbers",
            claude_response="I'll help you create an efficient Fibonacci function. Here's an implementation using dynamic programming...",
            tools_used=[
                {"name": "Write", "input": {"file": "fibonacci.py"}, "success": True}
            ]
        )

        # Log second interaction
        logger.log_interaction(
            user_prompt="Can you add type hints and documentation?",
            claude_response="I'll enhance the function with type hints and comprehensive documentation...",
            tools_used=[
                {"name": "Edit", "input": {"file": "fibonacci.py"}, "success": True}
            ]
        )

        # Log third interaction with multiple tools
        logger.log_interaction(
            user_prompt="Now let's test it",
            claude_response="I'll create a test file and run the tests to verify the implementation...",
            tools_used=[
                {"name": "Write", "input": {"file": "test_fibonacci.py"}, "success": True},
                {"name": "Bash", "input": {"command": "python -m pytest test_fibonacci.py"}, "success": True}
            ]
        )

    print("✅ Session logged to LangFuse!")


# Example 2: Manual session management
def example_manual_session():
    """Track interactions with manual session control"""

    logger = ClaudeCodeLogger(user_id="developer@example.com")

    # Start session
    session_id = logger.start_session({
        "project": "fibonacci_implementation",
        "goal": "Create well-tested Fibonacci function"
    })

    print(f"Started session: {session_id}")

    # Log interactions
    result = logger.log_interaction(
        user_prompt="Create a fibonacci function",
        claude_response="Here's an efficient implementation...",
        tools_used=[{"name": "Write", "success": True}],
        context={"task": "implementation"},
        duration_ms=1500
    )

    print(f"Interaction logged with trace ID: {result.get('trace_id')}")

    # Get dashboard URL
    trace_url = logger.get_trace_url()
    print(f"View trace at: {trace_url}")

    # End session
    stats = logger.end_session("Successfully implemented Fibonacci function")
    print(f"Session ended. Total interactions: {stats.get('total_interactions')}")


# Example 3: Quick logging without session
def example_quick_log():
    """Quick one-off logging"""

    from claude_logger import quick_log

    result = quick_log(
        prompt="What's the time complexity of bubble sort?",
        response="Bubble sort has a time complexity of O(n²) in the average and worst cases...",
        tools=None  # No tools used for this question
    )

    print(f"Quick log created: {result}")


if __name__ == "__main__":
    print("🎯 Claude Code Tracking Examples\n")

    print("1. Context Manager Example:")
    example_with_context_manager()
    print()

    print("2. Manual Session Example:")
    example_manual_session()
    print()

    print("3. Quick Log Example:")
    example_quick_log()

    print("\n✅ All examples completed!")
    print("📊 Check your traces at: http://localhost:3001")