import os
import sys
from contextlib import contextmanager


def tracing_configured():
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


class Trace:
    def __init__(self, span=None, callbacks=None, trace_id=None):
        self.span = span
        self.callbacks = callbacks or []
        self.trace_id = trace_id

    def finish(self, output):
        if self.span is not None:
            self.span.update(output=output)


def _connect():
    if not tracing_configured():
        return None

    try:
        from langfuse import get_client

        client = get_client()
        if not client.auth_check():
            print("Langfuse keys rejected, running without tracing.", file=sys.stderr)
            return None
        return client
    except Exception as error:
        print(f"Langfuse unavailable, running without tracing: {error}", file=sys.stderr)
        return None


@contextmanager
def start_trace(name, payload):
    client = _connect()
    if client is None:
        yield Trace()
        return

    from langfuse.langchain import CallbackHandler

    with client.start_as_current_observation(name=name, as_type="chain", input=payload) as span:
        yield Trace(span, [CallbackHandler()], client.get_current_trace_id())
    client.flush()
