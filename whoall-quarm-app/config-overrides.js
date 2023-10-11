module.exports = function override(config, env) {
    // Add a fallback for the Node.js built-in modules:
    config.resolve.fallback = {
        ...config.resolve.fallback,
        "path": require.resolve("path-browserify"),
        "fs": false  // This tells Webpack to provide an empty module for 'fs'
    };

        // Add a fallback for the crypto module
    if (!config.resolve.fallback) {
        config.resolve.fallback = {};
    }
    config.resolve.fallback["crypto"] = require.resolve("crypto-browserify");
    config.resolve.fallback["stream"] = require.resolve("stream-browserify");
    config.resolve.fallback["buffer"] = require.resolve("buffer/");

    return config;
};