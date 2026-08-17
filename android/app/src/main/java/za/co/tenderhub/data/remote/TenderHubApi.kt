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
 @GET("tenders") suspend fun tenders(@Query("q") q:String?=null,@Query("page") page:Int=1,@Query("page_size") pageSize:Int=20,@Query("province_id") provinceId:String?=null,@Query("district_id") districtId:String?=null,@Query("municipality_id") municipalityId:String?=null,@Query("category") category:String?=null,@Query("tender_type") tenderType:String?=null,@Query("status") status:String?=null,@Query("closing_from") closingFrom:String?=null,@Query("closing_to") closingTo:String?=null,@Query("issue_from") issueFrom:String?=null,@Query("issue_to") issueTo:String?=null,@Query("min_value") minValue:String?=null,@Query("max_value") maxValue:String?=null,@Query("sort") sort:String="relevance"):Page<Tender>
 @GET("tenders/{id}") suspend fun tender(@Path("id") id:String):TenderDetail
 @GET("provinces") suspend fun provinces():List<Province>
 @GET("districts") suspend fun districts():List<District>
 @GET("municipalities") suspend fun municipalities():List<Municipality>
 @POST("auth/password-reset/request") suspend fun requestPasswordReset(@Body body:PasswordResetRequest):PasswordResetRequested
 @POST("auth/password-reset/confirm") suspend fun confirmPasswordReset(@Body body:PasswordResetConfirm)
}
interface RefreshApi {@POST("auth/refresh") fun refresh(@Body body:RefreshRequest):Call<TokenResponse>}
