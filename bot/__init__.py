import sys

# Install telegram compatibility shims
import bot.utils.telegram_shim

# Install convenience module aliases
import bot.config as _config
import bot.database.db as _db
import bot.services.economy as _services
import bot.services.games as _games
import bot.keyboards.ui as _ui
import bot.utils.common as _common
import bot.utils.fill as _fill
import bot.utils.error_handler as _errors

sys.modules.setdefault("config", _config)
sys.modules.setdefault("db", _db)
sys.modules.setdefault("services", _services)
sys.modules.setdefault("games", _games)
sys.modules.setdefault("ui", _ui)
sys.modules.setdefault("ax_common", _common)
sys.modules.setdefault("ax_fill", _fill)
sys.modules.setdefault("ax_errors", _errors)
