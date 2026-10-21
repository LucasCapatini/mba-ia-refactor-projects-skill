// Remoção de usuário; matrículas e pagamentos saem junto pela cascata do schema.
const userModel = require('../models/user.model');

async function removeUser(db, userId) {
  return userModel.remove(db, userId);
}

module.exports = { removeUser };
