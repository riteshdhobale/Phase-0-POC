package com.railway.poc

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.*
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : AppCompatActivity() {

    // UI Components
    private lateinit var tvUserId: TextView
    private lateinit var tvWalletBalance: TextView
    private lateinit var tvJourneyStatus: TextView
    private lateinit var tvLastUpdate: TextView
    private lateinit var btnStartBle: Button
    private lateinit var btnStopBle: Button
    private lateinit var btnAddFunds: Button

    // Bluetooth
    private lateinit var bluetoothAdapter: BluetoothAdapter
    
    // SharedPreferences for persistent storage
    private lateinit var prefs: SharedPreferences
    
    // User data
    private var userId: String? = null
    private var previousBalance: Double = 100.0
    
    // Backend URL - CHANGE THIS TO YOUR MACBOOK IP
    private val BACKEND_URL = "http://192.168.31.187:8000"
    
    // Polling handler
    private val handler = Handler(Looper.getMainLooper())
    private var isPolling = false
    
    // Permission request code
    private val PERMISSION_REQUEST_CODE = 1001
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Initialize UI components
        initViews()
        
        // Initialize Bluetooth
        val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothAdapter = bluetoothManager.adapter
        
        // Initialize SharedPreferences
        prefs = getSharedPreferences("railway_poc", Context.MODE_PRIVATE)
        
        // Check if user is already registered
        userId = prefs.getString("user_id", null)
        
        if (userId == null) {
            // First launch - register user
            registerUser()
        } else {
            // Already registered - display user ID
            tvUserId.text = "User ID: ${userId?.take(8)}..."
            startWalletPolling()
        }
        
        // Button listeners
        btnStartBle.setOnClickListener {
            if (checkPermissions()) {
                startBleAdvertising()
            } else {
                requestPermissions()
            }
        }
        
        btnStopBle.setOnClickListener {
            stopBleAdvertising()
        }
        
        btnAddFunds.setOnClickListener {
            addFunds()
        }
    }
    
    private fun initViews() {
        tvUserId = findViewById(R.id.tvUserId)
        tvWalletBalance = findViewById(R.id.tvWalletBalance)
        tvJourneyStatus = findViewById(R.id.tvJourneyStatus)
        tvLastUpdate = findViewById(R.id.tvLastUpdate)
        btnStartBle = findViewById(R.id.btnStartBle)
        btnStopBle = findViewById(R.id.btnStopBle)
        btnAddFunds = findViewById(R.id.btnAddFunds)
    }
    
    private fun checkPermissions(): Boolean {
        val permissions = mutableListOf<String>()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            // Android 12+
            permissions.add(Manifest.permission.BLUETOOTH_ADVERTISE)
            permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            // Android 6-11
            permissions.add(Manifest.permission.BLUETOOTH)
            permissions.add(Manifest.permission.BLUETOOTH_ADMIN)
            permissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        
        // Android 13+ requires POST_NOTIFICATIONS for foreground service notification
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        
        return permissions.all {
            ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
        }
    }
    
    private fun requestPermissions() {
        val permissions = mutableListOf<String>()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            // Android 12+
            permissions.add(Manifest.permission.BLUETOOTH_ADVERTISE)
            permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            // Android 6-11
            permissions.add(Manifest.permission.BLUETOOTH)
            permissions.add(Manifest.permission.BLUETOOTH_ADMIN)
            permissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        
        // Android 13+ requires POST_NOTIFICATIONS for foreground service notification
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        
        ActivityCompat.requestPermissions(this, permissions.toTypedArray(), PERMISSION_REQUEST_CODE)
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                Toast.makeText(this, "Permissions granted", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Permissions required for BLE", Toast.LENGTH_LONG).show()
            }
        }
    }
    
    private fun registerUser() {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val url = URL("$BACKEND_URL/register_user")
                val connection = url.openConnection() as HttpURLConnection
                connection.requestMethod = "POST"
                connection.setRequestProperty("Content-Type", "application/json")
                
                val responseCode = connection.responseCode
                if (responseCode == HttpURLConnection.HTTP_OK) {
                    val response = connection.inputStream.bufferedReader().readText()
                    val jsonResponse = JSONObject(response)
                    val newUserId = jsonResponse.getString("user_id")
                    val balance = jsonResponse.getDouble("wallet_balance")
                    
                    // Save to SharedPreferences
                    prefs.edit().putString("user_id", newUserId).apply()
                    userId = newUserId
                    previousBalance = balance
                    
                    withContext(Dispatchers.Main) {
                        tvUserId.text = "User ID: ${newUserId.take(8)}..."
                        tvWalletBalance.text = "₹${balance.toInt()}"
                        Toast.makeText(
                            this@MainActivity,
                            "Registered successfully!",
                            Toast.LENGTH_SHORT
                        ).show()
                        startWalletPolling()
                    }
                } else {
                    withContext(Dispatchers.Main) {
                        Toast.makeText(
                            this@MainActivity,
                            "Registration failed: $responseCode",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    Toast.makeText(
                        this@MainActivity,
                        "Error: ${e.message}",
                        Toast.LENGTH_SHORT
                    ).show()
                    e.printStackTrace()
                }
            }
        }
    }
    
    private fun startBleAdvertising() {
        if (userId == null) {
            Toast.makeText(this, "User not registered yet", Toast.LENGTH_SHORT).show()
            return
        }
        
        val serviceIntent = Intent(this, BleAdvertisingService::class.java)
        serviceIntent.putExtra("USER_ID", userId)
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
        
        Toast.makeText(this, "BLE Advertising Started", Toast.LENGTH_SHORT).show()
        btnStartBle.isEnabled = false
        btnStopBle.isEnabled = true
    }
    
    private fun stopBleAdvertising() {
        val serviceIntent = Intent(this, BleAdvertisingService::class.java)
        stopService(serviceIntent)
        
        Toast.makeText(this, "BLE Advertising Stopped", Toast.LENGTH_SHORT).show()
        btnStartBle.isEnabled = true
        btnStopBle.isEnabled = false
    }
    
    private fun startWalletPolling() {
        if (isPolling) return
        isPolling = true
        
        val pollingRunnable = object : Runnable {
            override fun run() {
                fetchWalletBalance()
                handler.postDelayed(this, 5000) // Poll every 5 seconds
            }
        }
        
        handler.post(pollingRunnable)
    }
    
    private fun fetchWalletBalance() {
        if (userId == null) return
        
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val url = URL("$BACKEND_URL/wallet_balance?user_id=$userId")
                val connection = url.openConnection() as HttpURLConnection
                connection.requestMethod = "GET"
                
                val responseCode = connection.responseCode
                if (responseCode == HttpURLConnection.HTTP_OK) {
                    val response = connection.inputStream.bufferedReader().readText()
                    val jsonResponse = JSONObject(response)
                    val balance = jsonResponse.getDouble("wallet_balance")
                    val journeyActive = jsonResponse.getBoolean("journey_active")
                    
                    withContext(Dispatchers.Main) {
                        tvWalletBalance.text = "₹${balance.toInt()}"
                        tvJourneyStatus.text = if (journeyActive) {
                            "Journey: ACTIVE"
                        } else {
                            "Journey: NOT ACTIVE"
                        }
                        tvLastUpdate.text = "Updated: ${System.currentTimeMillis() / 1000}"
                        
                        // Check if balance decreased (fare deducted)
                        if (balance < previousBalance) {
                            val deducted = previousBalance - balance
                            Toast.makeText(
                                this@MainActivity,
                                "⚠️ Fare Deducted: ₹${deducted.toInt()}",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                        
                        previousBalance = balance
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
    
    private fun addFunds() {
        if (userId == null) return
        
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val url = URL("$BACKEND_URL/add_funds?user_id=$userId")
                val connection = url.openConnection() as HttpURLConnection
                connection.requestMethod = "POST"
                
                val responseCode = connection.responseCode
                if (responseCode == HttpURLConnection.HTTP_OK) {
                    val response = connection.inputStream.bufferedReader().readText()
                    val jsonResponse = JSONObject(response)
                    val newBalance = jsonResponse.getDouble("new_balance")
                    
                    withContext(Dispatchers.Main) {
                        tvWalletBalance.text = "₹${newBalance.toInt()}"
                        previousBalance = newBalance
                        Toast.makeText(
                            this@MainActivity,
                            "✅ ₹100 Added Successfully!",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    Toast.makeText(
                        this@MainActivity,
                        "Error adding funds: ${e.message}",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        isPolling = false
        handler.removeCallbacksAndMessages(null)
    }
}
