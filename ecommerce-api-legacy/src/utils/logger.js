'use strict';

const config = require('../config');

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const current = LEVELS[config.logLevel] ?? LEVELS.info;

const log = (level) => (...args) => {
    if (LEVELS[level] <= current) {
        const method = level === 'debug' ? 'log' : level;
        console[method](`[${level}]`, ...args);
    }
};

module.exports = {
    error: log('error'),
    warn: log('warn'),
    info: log('info'),
    debug: log('debug'),
};
