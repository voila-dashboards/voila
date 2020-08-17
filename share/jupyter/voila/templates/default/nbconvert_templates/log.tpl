{% macro js() %}
  <!-- voila log js -->
  <script>
    const _debug = console.debug;
    const _info = console.info;
    const _warn = console.warn;
    const _error = console.error;

    console.debug = (...args) => {
        window.top.postMessage({ level: "debug", msg: ["[VOILA]:", ...args] });
        _debug(...args);
    };

    console.info = console.info = (...args) => {
        window.top.postMessage({ level: "info", msg: ["[VOILA]:", ...args] });
        _info(...args);
    };

    console.warn = (...args) => {
        window.top.postMessage({ level: "warn", msg: ["[VOILA]:", ...args] });
        _warn(...args);
    };

    console.error = (...args) => {
        window.top.postMessage({ level: "error", msg: ["[VOILA]:", ...args] });
        _error(...args);
    };
  </script>
{% endmacro %}
