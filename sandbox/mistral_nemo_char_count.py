# ~/formalities/sandbox/mistral_nemo_char_count.py
import ollama
from formalities.utils.toolcalls import toolcallhandler

def mmtool(task: str, needs: list[str]) -> dict:
    """
    Discover logical frameworks and tools for solving formal reasoning tasks.

    Use this FIRST to find appropriate frameworks before attempting solutions.

    Args:
        task: Description of the reasoning task (e.g. "counting characters", "numeric validation")
        needs: Required logical capabilities (e.g. ["numeric", "successor_function", "formal_logic"])

    Returns:
        Available frameworks and components that match the requirements:
        {
            "available": [
                {
                    "name": "ClassicalFramework",  # Framework/component name
                    "type": "framework",           # Component type
                    "description": "..."           # Capabilities description
                }
            ]
        }
    """
    result = toolcallhandler._matchmaker({"task": task, "needs": needs})
    return result.data if result.success else {"error": result.error}

def mbtool(code: str, frameworks: list[str], validators: list[str], args: dict = {}) -> dict:
    """
    Build and validate logical constructs using formal reasoning frameworks.

    The code should define a function that constructs a formal logical solution using:
    - NumericProposition for representing countable values
    - Formal logic principles for computations
    - Valid proposition types that can be framework-validated

    Example for generic computation:
        code = '''
        from formalities.core.types.propositions import NumericProposition

        def compute_value(x: int) -> NumericProposition:
            # Start with base proposition
            base = NumericProposition("base", value=x)
            # Apply logical operations
            result = base + NumericProposition("step", value=1)
            return result
        '''

    Args:
        code: Python function implementing the logical construction
        frameworks: Required frameworks (e.g. ["ClassicalFramework"])
        validators: Validation strategies (e.g. ["LogicalConsistencyStrategy"])
        args: Arguments to pass to the function (e.g. {"x": 5}). THIS IS ABSOLUTELY MANDATORY IF THE FUNCTION TAKES ARGS AND KWARGS

    Returns:
        Validation results and computed value
    """
    result = toolcallhandler._methodbuilder({
        "code": code,
        "frameworks": frameworks,
        "validators": validators,
        "args": args
    })
    return result.data if result.success else {"error": result.error}

FUNCS = {
    'mmtool': mmtool,
    'mbtool': mbtool
}

def main():
    messages = [{
        'role': 'user',
        'content': "how many r's are there in strawberry? please be precise in your counting."
    }]

    # First interaction
    print("\n=== Initial Response ===")
    response = ollama.chat(model='mistral-nemo', messages=messages, tools=[mmtool, mbtool])
    print(f"{response}\n")

    # Process initial tool calls
    calls = response.message.tool_calls
    if calls:
        messages.append({
            'role': 'assistant',
            'content': response.message.content,
            'tool_calls': calls
        })

        for tool in calls:
            if (func := FUNCS.get(tool.function.name)):
                result = func(**tool.function.arguments)

                print(f"=== Tool Call: {tool.function.name} ===")
                if tool.function.name == 'mmtool':
                    print(f"Result: {str(result)[:100]}...")  # Truncate long mmtool results
                else:
                    print(f"Result: {result}")
                print()  # Empty line after result

                messages.append({
                    'role': 'tool',
                    'name': tool.function.name,
                    'content': str(result)
                })

                # Handle follow-up based on tool type and result
                if tool.function.name == 'mbtool' and 'error' in result:
                    followup_content = 'Please try again using formal logic and the successor function for counting. First discover available frameworks with mmtool.'
                elif tool.function.name == 'mmtool':
                    followup_content = 'Now that you have discovered the available frameworks, please implement a formal logic solution to count the characters.'
                else:
                    continue

                print("=== Follow-up Response ===")
                followup = ollama.chat(
                    model='mistral-nemo',
                    messages=messages + [{
                        'role': 'user',
                        'content': followup_content
                    }],
                    tools=[mmtool, mbtool]
                )
                print(f"{followup}\n")

                # Process follow-up tool calls
                if followup.message.tool_calls:
                    messages.append({
                        'role': 'assistant',
                        'content': followup.message.content,
                        'tool_calls': followup.message.tool_calls
                    })

                    for ftool in followup.message.tool_calls:
                        if (ffunc := FUNCS.get(ftool.function.name)):
                            fresult = ffunc(**ftool.function.arguments)

                            print(f"=== Follow-up Tool Call: {ftool.function.name} ===")
                            print(f"Result: {fresult}")
                            print()  # Empty line after result

                            messages.append({
                                'role': 'tool',
                                'name': ftool.function.name,
                                'content': str(fresult)
                            })
            else:
                print(f"!!! Unknown Tool Call: {tool.function.name} !!!\n")

if __name__ == "__main__":
    main()
