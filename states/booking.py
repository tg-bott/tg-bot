from aiogram.fsm.state import State, StatesGroup


class BookingFSM(StatesGroup):
    choosing_stage         = State()
    entering_quantity      = State()
    entering_username      = State()
    confirming             = State()

    choosing_edit_target   = State()
    editing_stage           = State()
    editing_quantity        = State()
    editing_username        = State()
    editing_confirm          = State()

    choosing_cancel_target  = State()
    confirming_cancel        = State()