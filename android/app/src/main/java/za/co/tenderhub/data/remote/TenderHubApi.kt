package za.co.tenderhub.data.remote
import retrofit2.Call
import retrofit2.http.*
import za.co.tenderhub.domain.model.*
interface TenderHubApi {
 @POST("auth/register") suspend fun register(@Body body:RegisterRequest):User
 @POST("auth/login") suspend fun login(@Body body:LoginRequest):TokenResponse
 @POST("auth/logout") suspend fun logout(@Body body:LogoutRequest)
 @GET("users/me") suspend fun me():User
 @GET("tenders/home") suspend fun home():HomeResponse
 @GET("tenders") suspend fun tenders(@Query("q") q:String?=null,@Query("page") page:Int=1,@Query("page_size") pageSize:Int=20,@Query("province_id") provinceId:String?=null,@Query("category") category:String?=null,@Query("status") status:String?=null,@Query("sort") sort:String="relevance"):Page<Tender>
 @GET("tenders/{id}") suspend fun tender(@Path("id") id:String):TenderDetail
 @GET("provinces") suspend fun provinces():List<Province>
}
interface RefreshApi {@POST("auth/refresh") fun refresh(@Body body:RefreshRequest):Call<TokenResponse>}
