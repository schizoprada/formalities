# ~/formalities/src/formalities/fall/runtime/shell.py
import os, cmd, sys, traceback, readline, re
from loguru import logger as log
PYGMENTSAVAILABLE = False

def importpygments():
    global PYGMENTSAVAILABLE
    global pygments, highlight, FALLLexer, formatter
    try:
        import pygments
        from pygments import highlight
        # Fix the RegexLexer import
        from pygments.lexer import RegexLexer
        from pygments.formatters import Terminal256Formatter, TerminalFormatter
        from pygments.token import Token

        # Define the FALLLexer class inside this function
        class FALLLexer(RegexLexer):
            """Custom lexer for FALL syntax highlighting."""
            name = 'FALL'
            aliases = ['fall']
            filenames = ['*.fall']

            tokens = {
                'root': [
                    # Comments
                    (r'!-.*?$', Token.Comment.Single),

                    # Keywords
                    (r'\b(DEFINE|RULE|AXIOM|WHERE|AS|IS|AND|OR|IMPLIES|CAN|BE|PROPOSITION|'
                     r'ASSERT|BEGIN|END|PROOF|STEP|INFER|FROM|VIA|GIVEN|PROVE|USING|QUERY)\b',
                     Token.Keyword),

                    # Double slash terminator
                    (r'//', Token.Operator),

                    # Strings
                    (r'"[^"]*"', Token.String),

                    # Identifiers
                    (r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', Token.Name),

                    # Numbers
                    (r'\b\d+\b', Token.Number),

                    # Whitespace
                    (r'\s+', Token.Text),

                    # Punctuation
                    (r'[\[\],:]', Token.Punctuation),
                ]
            }

        # Try to get 256 color support, fallback to 16 colors if needed
        try:
            # Use Terminal256Formatter with explicit style and force colorization
            formatter = Terminal256Formatter(style='monokai', bg='dark')
        except Exception:
            # Fallback to basic formatter
            formatter = TerminalFormatter(bg='dark')

        #print(f"Successfully imported Pygments v{pygments.__version__} from {pygments.__file__}", file=sys.stderr)
        PYGMENTSAVAILABLE = True
        return True
    except ImportError as e:
        print(f"Pygments Import Error: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"Python Path: {sys.path}", file=sys.stderr)
        PYGMENTSAVAILABLE = False
        print("Syntax Highlighting Disabled.")
        return False

importpygments()
from formalities.fall.parser.lexing import Lexer
from formalities.fall.parser.parsing import Parser
from formalities.fall.runtime.interpreter import Interpreter

def syntaxhighlight(code):
    """Apply syntax highlighting to FALL code."""
    if not PYGMENTSAVAILABLE:
        return code
    try:
        # Use our global formatter
        return highlight(code, FALLLexer(), formatter)
    except Exception as e:
        #log.error(f"Syntax highlighting failed: {str(e)}")
        return code

class FallShell(cmd.Cmd):
    intro = "FALL 0.1.0 (Formal Agnostic-Logic Language)"  # Empty intro to avoid showing it at startup
    prompt = 'FALL >>> '
    histfile = os.path.expanduser("~/.fallhistory")
    histfilesize = 1000
    debugmode = False

    def __init__(self):
        super().__init__()
        self.interpreter = Interpreter()
        # Keep track of multiline input
        self.buffer = []

        # Initialize readline history - handle permissions errors gracefully
        if readline:
            try:
                if os.path.exists(self.histfile):
                    readline.read_history_file(self.histfile)
                readline.set_history_length(self.histfilesize)
            except (IOError, OSError, PermissionError) as e:
                # Create a temporary history file in the current directory if we can't access the home one
                self.histfile = "./.fallhistory"
                #log.warning(f"Could not access history file in home directory: {str(e)}")
                #log.info(f"Using local history file: {self.histfile}")

    def preloop(self):
        """Hook method executed once when the cmdloop() method is called."""
        if readline:
            try:
                if os.path.exists(self.histfile):
                    readline.read_history_file(self.histfile)
            except (IOError, OSError, PermissionError):
                # Already handled in __init__
                pass

    def postloop(self):
        """Hook method executed once when the cmdloop() method is about to return."""
        if readline:
            try:
                readline.set_history_length(self.histfilesize)
                readline.write_history_file(self.histfile)
                print(f"Command history saved to {self.histfile}")
            except (IOError, OSError, PermissionError) as e:
                print(f"Could not save command history: {str(e)}")

    def default(self, line):
        """Handle any unrecognized command by treating it as FALL code."""
        # Add to readline history for multi-line input
        if line.strip() and readline:
            try:
                readline.add_history(line)
            except Exception:
                pass  # Ignore readline errors

        # Check if we've started a multi-line construct (like BEGIN PROOF)
        inmultiline = len(self.buffer) > 0 and any(l.strip().startswith("BEGIN") for l in self.buffer)
        startingmultiline = line.strip().startswith("BEGIN")
        endingmultiline = line.strip().startswith("END")

        # Add the current line to the buffer
        self.buffer.append(line)

        # Process if this is a complete statement
        if line.strip().endswith('//'):
            # Complete statement with terminator
            self._processbuffer()
        elif endingmultiline and line.strip().endswith('//'):
            # END of a multi-line construct with terminator
            self._processbuffer()
        elif not inmultiline and not startingmultiline:
            # Process immediately for simple statements without terminator (but not in multi-line mode)
            if not line.strip().startswith('DEFINE') and not line.strip().startswith('ASSERT'):
                self._processbuffer()
            else:
                # Continue collecting for certain statements that might be multi-line
                self.prompt = '.... >>> '
        else:
            # Continue collecting input
            self.prompt = '.... >>> '

    def _processbuffer(self):
        """Process the accumulated input buffer."""
        if not self.buffer:
            return

        # Special handling for proof blocks
        hasbeginproof = any('BEGIN PROOF' in line for line in self.buffer)
        hasendproof = any('END PROOF' in line for line in self.buffer)

        # For incomplete proof blocks, keep collecting
        if hasbeginproof and not hasendproof:
            self.prompt = '.... >>> '
            return

        # Process the buffer into a single source
        source = ' '.join(line.strip() for line in self.buffer)

        # Replace certain newline sequences for better parsing
        if hasbeginproof:
            # Make sure each part of the proof is properly separated
            source = source.replace('BEGIN PROOF', 'BEGIN PROOF //').replace('GIVEN', '// GIVEN')
            source = source.replace('PROVE', '// PROVE').replace('USING', '// USING')
            source = source.replace('STEP', '// STEP')
            source = source.replace('END PROOF', '// END PROOF')

        # Ensure // terminator
        if not source.strip().endswith('//'):
            source += ' //'

        # Clear buffer and reset prompt
        self.buffer = []
        self.prompt = 'FALL >>> '

        # Add to history
        if source.strip() and readline:
            try:
                readline.add_history(source)
            except Exception:
                pass  # Ignore readline errors

        # Debug the processed input with syntax highlighting
        if self.debugmode:
            print("\n--- Processing: ---")
            highlighted = syntaxhighlight(source)
            print(highlighted)

        try:
            # Lex phase
            lexer = Lexer(source)
            tokens = lexer.scantokens()

            # Extract for debugging
            token_types = [t.type.name for t in tokens]
            token_texts = [t.lexeme for t in tokens]

            if self.debugmode:
                print("\n--- Lexer Output ---")
                for i, token in enumerate(tokens):
                    print(f"{i}: {token.type.name:<15}: {token.lexeme}")

            # Parse phase
            parser = Parser(tokens)
            program = parser.parse()

            if self.debugmode:
                print("\n--- Parser Output ---")
                print(f"Program with {len(program.statements)} statements")
                for i, stmt in enumerate(program.statements):
                    print(f"  Statement {i+1}: {type(stmt).__name__}")

            # Interpret phase
            self.interpreter.interpret(program)

            # Display output
            output = self.interpreter.environment.getoutput()

            if self.debugmode:
                print("\n--- Interpreter Output ---")

            if output:
                print(output)
        except Exception as e:
            print(f"\n!!! Error: {str(e)}")
            if self.debugmode:
                traceback.print_exc()
            else:
                print("(Run with 'debug on' for more detailed error information)")
                print(f"Token types: {token_types}")
                print(f"Token texts: {token_texts}")

    def emptyline(self):
        """Handle empty lines."""
        if self.buffer:
            # If we have pending input, treat empty line as continuation
            self.buffer.append('')
        else:
            # Otherwise, do nothing
            pass

    def do_help(self, arg):
        """Show help information about FALL shell commands."""
        help_text = """
        FALL (Formal Agnostic Logic Language) Shell.
        Type help or ? for help, 'examples' for example commands, 'exit' to quit.

        Available commands:
        - help: Show this help message
        - examples: Show example FALL commands
        - debug [on|off]: Toggle debug mode
        - reset: Reset the interpreter state
        - exit: Exit the shell
        """
        print(help_text)

        # If an argument is provided, show help for that command
        if arg:
            # Use the default help behavior for specific commands
            super().do_help(arg)

    def do_exit(self, arg):
        """Exit the shell."""
        print("Goodbye!")
        return True

    def do_EOF(self, arg):
        """Exit on EOF (Ctrl+D)."""
        print("\nGoodbye!")
        return True

    def do_reset(self, arg):
        """Reset the interpreter environment."""
        self.interpreter = Interpreter()
        self.buffer = []
        print("Environment reset.")

    def do_debug(self, arg):
        """Toggle debug mode or set it explicitly (on/off)."""
        if arg.lower() == 'on':
            self.debugmode = True
        elif arg.lower() == 'off':
            self.debugmode = False
        else:
            # Toggle
            self.debugmode = not self.debugmode

        print(f"Debug mode: {'ON' if self.debugmode else 'OFF'}")

        # Configure log level based on debug mode
        if self.debugmode:
            #log.level("DEBUG")
            pass
        else:
            #log.level("INFO")
            pass

    def do_pygments(self, arg):
        """Check Pygments status."""
        if PYGMENTSAVAILABLE:
            print("Pygments is available. Syntax highlighting is enabled.")
            print(f"Pygments version: {pygments.__version__}")
        else:
            print("Pygments is not available. Syntax highlighting is disabled.")
            print("Try reinstalling with: pip install pygments")

    def do_examples(self, arg):
        """Show example FALL commands."""
        examples = [
            "# Define a simple rule",
            "DEFINE RULE SubjectPredicate WHERE SUBJECT CAN BE NOUN AND PREDICATE CAN BE VERB //",
            "",
            "# Define a proposition",
            "DEFINE PROPOSITION p AS \"The sky is blue\" WHERE \"sky\" IS SUBJECT AND \"blue\" IS PREDICATE //",
            "",
            "# Define an axiom",
            "DEFINE AXIOM ModusPonens WHERE p IMPLIES q AND p IS true //",
            "",
            "# Make an assertion",
            "ASSERT p //",
            "ASSERT p AND q //",
            "ASSERT p IMPLIES q //",
            "",
            "# Create a simple proof",
            "BEGIN PROOF",
            "GIVEN p",
            "PROVE q",
            "USING ModusPonens",
            "STEP 1: ASSERT p IMPLIES q",
            "STEP 2: INFER q FROM [p] VIA ModusPonens",
            "END PROOF //",
            "",
            "# Make a query",
            "QUERY p //",
        ]
        print("\nFALL Examples:")
        print("-------------")

        # Print examples with syntax highlighting if available
        for example in examples:
            if example.strip() and not example.startswith('#') and PYGMENTSAVAILABLE:
                print(syntaxhighlight(example))
            else:
                print(example)

        print("\nTo use an example, copy and paste it into the shell.")

    # Add this to the shell.py file, replacing or modifying the existing do_bridge method
    def do_bridge(self, arg):
        """
        Activate or configure a bridge component.
        Usage: BRIDGE <component> [ON|OFF|<parameter> <value>]
        """
        parts = arg.strip().split()
        if not parts:
            print("Usage: BRIDGE <component> [ON|OFF|<parameter> <value>]")
            return

        component = parts[0].upper()

        if component == "NLP":
            # Import only when needed
            from formalities.fall.bridges.nlp import NLPBridge

            # Create or get bridge
            if not hasattr(self.interpreter.environment, 'nlpbridge'):
                self.interpreter.environment.nlpbridge = NLPBridge()

            bridge = self.interpreter.environment.nlpbridge

            # Also connect to logic bridge
            if hasattr(self.interpreter.environment, 'bridge'):
                self.interpreter.environment.bridge.nlpbridge = bridge

            if len(parts) == 1:
                # Just BRIDGE NLP, report status
                status = "ENABLED" if bridge.enabled else "DISABLED"
                print(f"NLP Bridge is currently {status} (threshold: {bridge.simthresh:.2f})")
                return

            action = parts[1].upper()

            if action == "ON":
                try:
                    result = bridge.enable()
                    print(result)  # Print the result directly

                    # Make sure the bridge object is properly connected to the logic bridge
                    if hasattr(self.interpreter.environment, 'bridge'):
                        self.interpreter.environment.bridge.nlpbridge = bridge
                        print(f"Connected NLP bridge to logic bridge (enabled={bridge.enabled})")
                except Exception as e:
                    print(f"Failed to enable NLP Bridge: {str(e)}")
            elif action == "OFF":
                result = bridge.disable()
                print(result)  # Print the result directly
            elif action == "THRESHOLD" and len(parts) >= 3:
                try:
                    threshold = float(parts[2])
                    result = bridge.setsimthresh(threshold)
                    print(result)  # Print the result directly
                except ValueError:
                    print(f"Invalid threshold value: {parts[2]}. Must be a number between 0.0 and 1.0")
            else:
                print(f"Unknown NLP Bridge action: {action}")
        else:
            print(f"Unknown bridge component: {component}")

    def do_symbolize(self, arg):
        """
        Symbolize a proposition into formal logical notation.
        Usage: SYMBOLIZE <proposition_name>
        """
        propname = arg.strip()
        if not propname:
            print("Usage: SYMBOLIZE <proposition_name>")
            return

        env = self.interpreter.environment

        # Check for proposition
        prop = None
        if hasattr(env, 'bridge'):
            prop = env.bridge.getprop(propname)

        if not prop:
            print(f"[red]Unknown proposition: {propname}[/red]")
            return

        # Use NLP bridge if available
        if hasattr(env, 'nlpbridge'):
            bridge = env.nlpbridge

            if not bridge.enabled:
                print("[yellow]NLP Bridge is disabled. Enabling NLP Bridge may provide better symbolization.[/yellow]")

            symbolic = bridge.symbolize(prop)
            print(f"[blue]Symbolic representation of {propname}:[/blue] {symbolic}")
        else:
            print("[yellow]NLP Bridge not available. Use 'BRIDGE NLP ON' for symbolization.[/yellow]")


def main():
    """Run the FALL shell."""
    # Add command line arguments support
    import argparse

    parser = argparse.ArgumentParser(description='FALL - Formal Agnostic Logic Language')
    parser.add_argument('-f', '--file', help='Execute FALL script from file')
    parser.add_argument('-c', '--command', help='Execute a single FALL command')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Check Pygments at startup
    if PYGMENTSAVAILABLE:
        #print(f"Syntax highlighting enabled (Pygments v{pygments.__version__})")
        pass
    else:
        print("Syntax highlighting disabled. Install pygments with: pip install pygments")

    try:
        if args.file:
            # Execute script from file
            with open(args.file, 'r') as f:
                content = f.read()
                interpreter = Interpreter()
                lexer = Lexer(content)
                tokens = lexer.scantokens()
                parser = Parser(tokens)
                program = parser.parse()
                interpreter.interpret(program)
                print(interpreter.environment.getoutput())
        elif args.command:
            # Execute a single command
            interpreter = Interpreter()
            lexer = Lexer(args.command)
            tokens = lexer.scantokens()
            parser = Parser(tokens)
            program = parser.parse()
            interpreter.interpret(program)
            print(interpreter.environment.getoutput())
        else:
            # Run interactive shell
            shell = FallShell()
            shell.debugmode = args.debug
            shell.cmdloop()
    except KeyboardInterrupt:
        print("\nTerminating.")
        # Make sure to save history on CTRL+C
        if readline:
            try:
                shell = locals().get('shell')
                if shell:
                    readline.write_history_file(shell.histfile)
            except Exception:
                pass
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        if args and args.debug:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
