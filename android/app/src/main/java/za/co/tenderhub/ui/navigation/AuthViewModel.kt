package za.co.tenderhub.ui.navigation
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import za.co.tenderhub.data.repository.*
import za.co.tenderhub.domain.model.User
sealed interface AuthState { data object Loading:AuthState; data object Anonymous:AuthState; data class Authenticated(val user:User):AuthState; data class Error(val message:String):AuthState }
class AuthViewModel(private val repository:AuthRepository):ViewModel(){
 private val _state=MutableStateFlow<AuthState>(AuthState.Loading);val state:StateFlow<AuthState> =_state.asStateFlow()
 init{viewModelScope.launch{repository.invalidations.collect{_state.value=AuthState.Anonymous}};restore()}; fun restore()=viewModelScope.launch{_state.value=when(val r=repository.restore()){is ApiResult.Success->AuthState.Authenticated(r.value);is ApiResult.Error->AuthState.Anonymous}}
 fun login(email:String,password:String)=viewModelScope.launch{_state.value=AuthState.Loading;_state.value=when(val r=repository.login(email,password)){is ApiResult.Success->AuthState.Authenticated(r.value);is ApiResult.Error->AuthState.Error(r.message)}}
 fun register(email:String,password:String,first:String,last:String)=viewModelScope.launch{_state.value=AuthState.Loading;_state.value=when(val r=repository.register(email,password,first,last)){is ApiResult.Success->when(val login=repository.login(email,password)){is ApiResult.Success->AuthState.Authenticated(login.value);is ApiResult.Error->AuthState.Error(login.message)};is ApiResult.Error->AuthState.Error(r.message)}}
 fun logout()=viewModelScope.launch{repository.logout();_state.value=AuthState.Anonymous}
}
class PasswordResetViewModel(private val repository:za.co.tenderhub.data.repository.AuthRepository):androidx.lifecycle.ViewModel(){
 sealed interface State{data object Form:State;data object Loading:State;data class Requested(val developmentToken:String?):State;data object Complete:State;data class Error(val message:String):State}
 private val _state=kotlinx.coroutines.flow.MutableStateFlow<State>(State.Form);val state:kotlinx.coroutines.flow.StateFlow<State> =_state
 fun request(email:String)=viewModelScope.launch{_state.value=State.Loading;_state.value=when(val result=repository.requestPasswordReset(email)){is za.co.tenderhub.data.repository.ApiResult.Success->State.Requested(result.value.development_token);is za.co.tenderhub.data.repository.ApiResult.Error->State.Error(result.message)}}
 fun confirm(token:String,password:String)=viewModelScope.launch{_state.value=State.Loading;_state.value=when(val result=repository.confirmPasswordReset(token,password)){is za.co.tenderhub.data.repository.ApiResult.Success->State.Complete;is za.co.tenderhub.data.repository.ApiResult.Error->State.Error(result.message)}}
}
