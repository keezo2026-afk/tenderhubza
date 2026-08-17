package za.co.tenderhub.data.remote
import retrofit2.http.*
import za.co.tenderhub.domain.model.*
interface TenderHubApi {
 @POST("auth/register") suspend fun register(@Body body:RegisterRequest):User
 @POST("auth/login") suspend fun login(@Body body:LoginRequest):TokenResponse
 @POST("auth/logout") suspend fun logout()
 @GET("users/me") suspend fun me():User
 @GET("tenders") suspend fun tenders(@Query("page") page:Int=1):Page<Tender>
}
