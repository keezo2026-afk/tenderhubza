package za.co.tenderhub.data.repository
import retrofit2.HttpException
import za.co.tenderhub.core.auth.TokenStore
import za.co.tenderhub.data.remote.TenderHubApi
import za.co.tenderhub.domain.model.*
sealed interface ApiResult<out T>{data class Success<T>(val value:T):ApiResult<T>;data class Error(val message:String,val status:Int?=null):ApiResult<Nothing>}
interface AuthRepository { suspend fun restore():ApiResult<User>; suspend fun login(email:String,password:String):ApiResult<User>; suspend fun register(email:String,password:String,first:String,last:String):ApiResult<User>; suspend fun logout() }
class NetworkAuthRepository(private val api:TenderHubApi,private val tokens:TokenStore):AuthRepository {
 private suspend fun <T> safe(block:suspend()->T):ApiResult<T> = try{ApiResult.Success(block())}catch(e:HttpException){ApiResult.Error(if(e.code()==401)"Email or password is incorrect" else "Request failed. Please try again.",e.code())}catch(e:Exception){ApiResult.Error("Unable to connect to TenderHub SA")}
 override suspend fun restore()=if(tokens.get()==null) ApiResult.Error("No session",401) else safe{api.me()}
 override suspend fun login(email:String,password:String):ApiResult<User>{ return when(val result=safe{api.login(LoginRequest(email,password))}){is ApiResult.Success->{tokens.set(result.value.access_token);restore()};is ApiResult.Error->result} }
 override suspend fun register(email:String,password:String,first:String,last:String)=safe{api.register(RegisterRequest(email,password,first,last))}
 override suspend fun logout(){try{api.logout()}catch(_:Exception){}finally{tokens.clear()}}
}
