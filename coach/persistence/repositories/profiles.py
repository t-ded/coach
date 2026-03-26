from typing import Any
from typing import Optional
from typing import cast

from postgrest import SyncRequestBuilder
from supabase import Client

from coach.domain.profile import UserProfile
from coach.persistence.serialization import deserialize_goal
from coach.persistence.serialization import serialize_goal
from coach.reasoning.providers import LLMProvider

type ProfileRow = dict[str, Any]


class SupabaseUserProfileRepository:
    TABLE = 'profiles'

    def __init__(self, client: Client, user_id: str) -> None:
        self._db = client
        self._user_id = user_id

    def _table(self) -> SyncRequestBuilder:
        return self._db.table(self.TABLE)

    def load(self) -> Optional[UserProfile]:
        response = self._table().select('*').eq('user_id', self._user_id).maybe_single().execute()
        if not response or not response.data:
            return None
        return self._from_row(cast(ProfileRow, response.data))

    def save(self, profile: UserProfile) -> None:
        self._table().upsert(self._to_row(profile), on_conflict='user_id').execute()

    def delete(self) -> None:
        self._table().delete().eq('user_id', self._user_id).execute()

    def set_preferred_provider(self, provider: LLMProvider) -> None:
        self._table().update({'preferred_provider': provider}).eq('user_id', self._user_id).execute()

    def _to_row(self, profile: UserProfile) -> ProfileRow:
        return {
            'user_id': self._user_id,
            'chat_preferences': profile.chat_preferences,
            'training_preferences': profile.training_preferences,
            'personal_information': profile.personal_information,
            'constraints': profile.constraints,
            'goals': [serialize_goal(goal) for goal in profile.goals] if profile.goals is not None else None,
        }

    @staticmethod
    def _from_row(row: ProfileRow) -> UserProfile:
        goals_raw = row.get('goals')
        return UserProfile(
            chat_preferences=row.get('chat_preferences'),
            training_preferences=row.get('training_preferences'),
            personal_information=row.get('personal_information'),
            constraints=row.get('constraints'),
            goals=tuple(deserialize_goal(goal) for goal in goals_raw) if goals_raw is not None else None,
        )
