# ~/formalities/sandbox/mistralnemo/managed_char_count.py
import ollama
import sys
import json
from pathlib import Path

# Add the parent directory to sys.path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from formalities.utils.toolcalls import toolcallhandler
from formalities.utils.dialog.controller import dialogcontroller, DialogRequest, DialogResponse, DialogAction
from formalities.utils.integrations import setupintegrations
from loguru import logger as log

# Configure logging
log.remove()
log.add(sys.stderr, level="INFO")
log.add("./dialog_mistral_test.log", rotation="1 MB", level="DEBUG")

# Initialize integrations
setupintegrations()

def mmtool(task: str, needs: list[str]) -> dict:
    """
    Discover logical frameworks and tools for solving formal reasoning tasks.
    """
    try:
        # Process through dialog controller for error handling
        result = dialogcontroller.handletoolcall("matchmaker", {"task": task, "needs": needs})
        dialogcontroller.state.memory.addtoolcall("mmtool", {"task": task, "needs": needs}, result, "error" not in result)
        return result
    except Exception as e:
        log.error(f"Error in mmtool: {str(e)}")
        dialogcontroller.state.seterror(e)
        return {"error": str(e)}

def mbtool(code: str, frameworks: list[str], validators: list[str], args: dict = {}) -> dict:
    """
    Build and validate logical constructs using formal reasoning frameworks.
    """
    try:
        # Process through dialog controller for error handling
        result = dialogcontroller.handletoolcall("methodbuilder", {
            "code": code,
            "frameworks": frameworks,
            "validators": validators,
            "args": args
        })

        # Record tool call in dialog memory
        toolargs = {
            "code": "..." if len(code) > 100 else code,  # Truncate long code for memory
            "frameworks": frameworks,
            "validators": validators,
            "args": args
        }
        dialogcontroller.state.memory.addtoolcall("mbtool", toolargs, result, "error" not in result)

        return result
    except Exception as e:
        log.error(f"Error in mbtool: {str(e)}")
        dialogcontroller.state.seterror(e)
        return {"error": str(e)}

FUNCS = {
    'mmtool': mmtool,
    'mbtool': mbtool
}

def process_message(message: str, context=None) -> str:
    """Process a message through the dialog controller"""
    request = DialogRequest(content=message, metadata=context or {})
    response = dialogcontroller.processrequest(request)

    # If there are suggested tools, append them to the message
    suggestion_text = ""
    if response.suggestedtools:
        suggestion_text = f"\n\nI recommend using these tools: {', '.join(response.suggestedtools)}"

    return response.content + suggestion_text

def process_tool_call(tool_name, args, messages):
    """Process a tool call and manage follow-up responses"""
    # Execute the tool call
    result = FUNCS[tool_name](**args)

    # Log the result
    print(f"=== Tool Call: {tool_name} ===")
    if tool_name == 'mmtool':
        print(f"Result: {str(result)[:100]}...")  # Truncate long mmtool results
    else:
        print(f"Result: {result}")
    print()  # Empty line after result

    # Add to message history
    messages.append({
        'role': 'tool',
        'name': tool_name,
        'content': str(result)
    })

    return result, messages

def main():
    log.info("Starting managed dialog test with Mistral-Nemo")

    # Initial state setup
    dialogcontroller.state.transitionto(dialogcontroller.state.stage)  # Reset to initial stage

    # Initial message
    messages = [{
        'role': 'user',
        'content': "how many r's are there in strawberry? please be precise in your counting."
    }]

    # Track success
    success = False
    max_iterations = 5
    current_iteration = 0
    final_answer = None

    while not success and current_iteration < max_iterations:
        current_iteration += 1
        print(f"\n=== ITERATION {current_iteration} ===")

        # Get model response
        print("\n=== Model Response ===")
        response = ollama.chat(model='mistral-nemo', messages=messages, tools=[mmtool, mbtool])
        print(f"{response}\n")

        # Add model response to messages
        has_tool_calls = hasattr(response.message, 'tool_calls') and response.message.tool_calls
        messages.append({
            'role': 'assistant',
            'content': response.message.content,
            'tool_calls': response.message.tool_calls if has_tool_calls else []
        })

        # If no tool calls and we have content, we might have an answer
        if not has_tool_calls and response.message.content.strip():
            print("Direct answer provided without tools.")
            if current_iteration == 1:
                # First response - ask to use tools
                messages.append({
                    'role': 'user',
                    'content': "Please solve this using formal logic. Use mmtool first to discover the available frameworks and components."
                })
                continue  # Go to next iteration
            else:
                # Later response - might be our final answer
                print("=== Final Answer (Direct) ===")
                print(response.message.content)
                final_answer = response.message.content
                break

        # Process tool calls
        if has_tool_calls:
            all_successful = True

            for tool in response.message.tool_calls:
                if tool.function.name in FUNCS:
                    # Process tool call
                    result, messages = process_tool_call(tool.function.name, tool.function.arguments, messages)

                    # Check if there was an error
                    if 'error' in result:
                        all_successful = False

                        # Process the error through dialog management
                        dialog_response = process_message(
                            f"I encountered an error when using {tool.function.name}: {result['error']}",
                            {"tool": tool.function.name, "error": result['error']}
                        )

                        # Show dialog system response
                        print("=== Dialog Management Response ===")
                        print(dialog_response)
                        print()

                        # Add error guidance to messages for next iteration
                        messages.append({
                            'role': 'user',
                            'content': f"There was an error: {result['error']}. {dialog_response} Please try again."
                        })
                    elif tool.function.name == 'mbtool' and 'result' in result:
                        # Successful method builder - we have a result!
                        print("=== Successful Execution! ===")
                        success = True

                        # Request final answer explanation
                        messages.append({
                            'role': 'user',
                            'content': "Great! Based on this result, can you tell me how many r's are in 'strawberry'?"
                        })

                        # Get final answer
                        final = ollama.chat(model='mistral-nemo', messages=messages)

                        print("\n=== Final Answer ===")
                        print(final.message.content)
                        final_answer = final.message.content
                        break
                else:
                    print(f"!!! Unknown Tool Call: {tool.function.name} !!!\n")
                    all_successful = False

            # If all tool calls were successful but no final result yet, add guidance for next step
            if all_successful and not success:
                if any(tc.function.name == 'mmtool' for tc in response.message.tool_calls):
                    # After successful matchmaker, suggest implementing counting
                    dialog_guidance = process_message(
                        "The matchmaker tool call was successful. What should I do next?",
                        {"success": True, "tool": "mmtool"}
                    )

                    print("=== Dialog Management Guidance ===")
                    print(dialog_guidance)
                    print()

                    messages.append({
                        'role': 'user',
                        'content': "Great! Now please implement a function that uses AtomicProposition and " +
                                  "NumericProposition to count the r's in 'strawberry'. Use the mbtool to validate your solution."
                    })

        # If no tool calls were made but we expected them, guide the model
        elif current_iteration == 1:
            print("No tool calls were made. The model provided a direct answer.")
            messages.append({
                'role': 'user',
                'content': "Please solve this using formal logic. Use mmtool first to discover the available frameworks and components."
            })

    # Report final status
    if success:
        print("\n=== SUCCESS! ===")
        print(f"Successfully completed after {current_iteration} iterations")
    else:
        print("\n=== MAX ITERATIONS REACHED ===")
        print(f"Could not complete successfully after {max_iterations} iterations")

    if final_answer:
        print("\n=== FINAL ANSWER ===")
        print(final_answer)

    # Report dialog statistics
    log.info(f"Dialog completed with {len(dialogcontroller.state.history.exchanges)} exchanges")
    log.info(f"Tool calls: {len(dialogcontroller.state.memory.toolcalls)}")
    log.info(f"Final dialog stage: {dialogcontroller.state.stage.name}")

    # Reset dialog controller for next use
    dialogcontroller.reset()

if __name__ == "__main__":
    main()
