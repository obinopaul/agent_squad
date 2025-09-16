import inspect
from functools import wraps
from typing import Callable

# from langchain_core._api import beta
from langchain_core.tools import tool

def convert_positional_only_function_to_tool(func: Callable):
    """
    Wraps a function with positional-only arguments to make it compatible
    with LangChain's tool creation, which requires keyword arguments.
    
    This utility inspects the function's signature and transforms any
    positional-only parameters into standard positional-or-keyword
    parameters. This allows functions from libraries like `math` to be
    seamlessly converted into tools.
    """
    try:
        original_signature = inspect.signature(func)
    except ValueError:  # Handles cases where a signature cannot be determined
        return None

    new_params = []
    has_positional_only = False

    # Iterate through the original parameters to rebuild the signature
    for param in original_signature.parameters.values():
        # Reject functions with variable positional arguments (*args)
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            return None
            
        # Convert positional-only parameters to positional-or-keyword
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            has_positional_only = True
            new_params.append(
                param.replace(kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
            )
        else:
            new_params.append(param)

    # If no positional-only arguments were found, no need to wrap
    if not has_positional_only:
        return tool(func)

    updated_signature = inspect.Signature(new_params)

    @wraps(func)
    def wrapper(*args, **kwargs):
        """The wrapped function that now accepts keyword arguments."""
        # Bind the provided arguments to the new signature
        bound = updated_signature.bind(*args, **kwargs)
        bound.apply_defaults()
        # Call the original function with the correctly ordered arguments
        return func(*bound.args, **bound.kwargs)

    # Override the signature of the wrapper
    wrapper.__signature__ = updated_signature

    return tool(wrapper)