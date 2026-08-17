package za.co.tenderhub.ui.screens
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import za.co.tenderhub.data.repository.*
import za.co.tenderhub.domain.model.*
class NotificationViewModel(private val repo:NotificationRepository):ViewModel(){private val _state=MutableStateFlow<DataState<List<TenderNotification>>>(DataState.Loading);val state:StateFlow<DataState<List<TenderNotification>>> =_state;private val _unread=MutableStateFlow(0);val unread:StateFlow<Int> =_unread
 fun load()=viewModelScope.launch{_state.value=DataState.Loading;_state.value=when(val r=repo.list()){is ApiResult.Success->if(r.value.items.isEmpty())DataState.Empty else DataState.Success(r.value.items);is ApiResult.Error->DataState.Error(r.message)};refreshUnread()};fun refreshUnread()=viewModelScope.launch{when(val r=repo.unread()){is ApiResult.Success->_unread.value=r.value;is ApiResult.Error->Unit}};fun read(item:TenderNotification,onTender:(String)->Unit)=viewModelScope.launch{when(val result=repo.read(item.id)){is ApiResult.Success->{val current=(_state.value as? DataState.Success)?.data.orEmpty();_state.value=DataState.Success(current.map{if(it.id==item.id)result.value else it})};is ApiResult.Error->Unit};refreshUnread();item.tender_id?.let(onTender)};fun readAll()=viewModelScope.launch{repo.readAll();load()}}
class NotificationSettingsViewModel(private val repo:NotificationRepository):ViewModel(){private val _state=MutableStateFlow<DataState<NotificationPreference>>(DataState.Loading);val state:StateFlow<DataState<NotificationPreference>> =_state;fun load()=viewModelScope.launch{_state.value=DataState.Loading;_state.value=when(val r=repo.preferences()){is ApiResult.Success->DataState.Success(r.value);is ApiResult.Error->DataState.Error(r.message)}};fun save(value:NotificationPreferenceInput)=viewModelScope.launch{_state.value=DataState.Loading;_state.value=when(val r=repo.update(value)){is ApiResult.Success->DataState.Success(r.value);is ApiResult.Error->DataState.Error(r.message)}}}
