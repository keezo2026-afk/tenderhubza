package za.co.tenderhub.data.repository
import kotlinx.coroutines.flow.SharedFlow
import retrofit2.HttpException
import za.co.tenderhub.core.auth.TokenStore
import za.co.tenderhub.data.remote.TenderHubApi
import za.co.tenderhub.domain.model.*
sealed interface ApiResult<out T>{data class Success<T>(val value:T):ApiResult<T>;data class Error(val message:String,val status:Int?=null):ApiResult<Nothing>}
internal suspend fun <T> apiCall(block:suspend()->T):ApiResult<T> =try{ApiResult.Success(block())}catch(e:HttpException){ApiResult.Error(if(e.code()==401)"Your session has expired. Please log in again." else "Request failed. Please try again.",e.code())}catch(e:Exception){ApiResult.Error("Unable to connect to TenderHub SA")}
interface AuthRepository {val invalidations:SharedFlow<Unit>;suspend fun restore():ApiResult<User>;suspend fun login(email:String,password:String):ApiResult<User>;suspend fun register(email:String,password:String,first:String,last:String):ApiResult<User>;suspend fun logout();suspend fun requestPasswordReset(email:String):ApiResult<PasswordResetRequested>;suspend fun confirmPasswordReset(token:String,password:String):ApiResult<Unit>}
class NetworkAuthRepository(private val api:TenderHubApi,private val tokens:TokenStore):AuthRepository {
 override val invalidations=tokens.invalidations
 override suspend fun restore()=if(tokens.access()==null)ApiResult.Error("No session",401)else apiCall{api.me()}
 override suspend fun login(email:String,password:String):ApiResult<User>{return when(val result=apiCall{api.login(LoginRequest(email,password))}){is ApiResult.Success->{tokens.set(result.value.access_token,result.value.refresh_token);restore()};is ApiResult.Error->result}}
 override suspend fun register(email:String,password:String,first:String,last:String)=apiCall{api.register(RegisterRequest(email,password,first,last))}
 override suspend fun logout(){try{api.logout(LogoutRequest(tokens.refresh()))}catch(_:Exception){}finally{tokens.clear()}}
 override suspend fun requestPasswordReset(email:String)=apiCall{api.requestPasswordReset(PasswordResetRequest(email))}
 override suspend fun confirmPasswordReset(token:String,password:String)=apiCall{api.confirmPasswordReset(PasswordResetConfirm(token,password))}
}
