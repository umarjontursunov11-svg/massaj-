from aiogram.fsm.state import State, StatesGroup

class BookingState(StatesGroup):
    """Qabulga yozilish bosqichlari"""
    selecting_branch = State()
    entering_parent_name = State()
    entering_child_name = State()
    entering_phone = State()
    selecting_date = State()
    selecting_time = State()
    confirming = State()

class AdminBroadcastState(StatesGroup):
    """Admin yangilik va e'lon tarqatish holati"""
    waiting_for_content = State()
    confirming_broadcast = State()

class AdminBranchEditState(StatesGroup):
    """Admin filial ma'lumotlarini tahrirlash holatlari"""
    editing_phone = State()
    editing_address = State()
    editing_landmark = State()
    editing_working_hours = State()
    editing_location = State()

class CourseApplicationState(StatesGroup):
    """O'quv kursi arizasini to'ldirish bosqichlari"""
    entering_name = State()
    entering_phone = State()
    confirming = State()


