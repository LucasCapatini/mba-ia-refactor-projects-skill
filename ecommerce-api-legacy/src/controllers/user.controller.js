// HTTP ↔ usuários.
const { validateUserId } = require('../validators/user.validator');
const userService = require('../services/user.service');

function createUserController({ db }) {
  return {
    async remove(req, res) {
      const userId = validateUserId(req.params);
      await userService.removeUser(db, userId);
      res.send('Usuário deletado');
    },
  };
}

module.exports = { createUserController };
