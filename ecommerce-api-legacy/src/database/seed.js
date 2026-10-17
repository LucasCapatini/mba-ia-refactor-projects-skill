'use strict';

const config = require('../config');
const logger = require('../utils/logger');
const { hashPassword } = require('../utils/password');
const { PAYMENT_STATUS } = require('../domain/constants');
const userModel = require('../models/user.model');
const courseModel = require('../models/course.model');
const enrollmentModel = require('../models/enrollment.model');
const paymentModel = require('../models/payment.model');

/** Popula os dados iniciais apenas quando o banco está vazio. */
async function seed(db) {
    const { total } = await db.get('SELECT COUNT(*) AS total FROM courses');
    if (total > 0) return { seeded: false };

    await db.transaction(async () => {
        const userId = await userModel.create(db, {
            name: 'Leonan',
            email: 'leonan@fullcycle.com.br',
            passwordHash: hashPassword('123'),
        });
        const cleanArchId = await courseModel.create(db, { title: 'Clean Architecture', price: 997.00, active: 1 });
        await courseModel.create(db, { title: 'Docker', price: 497.00, active: 1 });
        const enrollmentId = await enrollmentModel.create(db, userId, cleanArchId);
        await paymentModel.create(db, enrollmentId, 997.00, PAYMENT_STATUS.PAID);
    });

    return { seeded: true };
}

async function countRows(db) {
    const tables = ['users', 'courses', 'enrollments', 'payments', 'audit_logs'];
    const counts = {};
    for (const table of tables) {
        const row = await db.get(`SELECT COUNT(*) AS total FROM ${table}`);
        counts[table] = row.total;
    }
    return counts;
}

async function main() {
    const { connect } = require('./connection');
    const { createTables } = require('./schema');
    const db = await connect(config.dbPath);
    try {
        await createTables(db);
        const result = await seed(db);
        logger.info(result.seeded ? 'Seed aplicado.' : 'Banco já populado; seed ignorado.');
        logger.info('Registros por tabela:', await countRows(db));
    } finally {
        await db.close();
    }
}

if (require.main === module) {
    main().catch((err) => {
        logger.error('Falha ao executar o seed', err);
        process.exit(1);
    });
}

module.exports = { seed, countRows };
