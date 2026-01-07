package com.railway.poc

import android.app.*
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.AdvertiseCallback
import android.bluetooth.le.AdvertiseData
import android.bluetooth.le.AdvertiseSettings
import android.bluetooth.le.BluetoothLeAdvertiser
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.ParcelUuid
import androidx.core.app.NotificationCompat
import java.nio.charset.StandardCharsets
import java.util.*

class BleAdvertisingService : Service() {

    private var bluetoothLeAdvertiser: BluetoothLeAdvertiser? = null
    private var userId: String? = null
    
    companion object {
        private const val CHANNEL_ID = "BleAdvertisingChannel"
        private const val NOTIFICATION_ID = 1001
        
        // Custom service UUID for our POC
        private val SERVICE_UUID = UUID.fromString("0000FFF0-0000-1000-8000-00805F9B34FB")
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        
        val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        val bluetoothAdapter = bluetoothManager.adapter
        bluetoothLeAdvertiser = bluetoothAdapter?.bluetoothLeAdvertiser
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        userId = intent?.getStringExtra("USER_ID")
        
        if (userId == null) {
            stopSelf()
            return START_NOT_STICKY
        }
        
        // Start foreground service with notification
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)
        
        // Start BLE advertising
        startAdvertising()
        
        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Railway BLE Service",
                NotificationManager.IMPORTANCE_HIGH  // Changed to HIGH for visibility
            ).apply {
                description = "BLE advertising for railway ticketing"
                setShowBadge(true)
            }
            
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        val notificationIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            notificationIntent,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            } else {
                PendingIntent.FLAG_UPDATE_CURRENT
            }
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("🚂 Railway BLE Active")
            .setContentText("Broadcasting your ticket - DO NOT close!")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
            .build()
    }

    private fun startAdvertising() {
        if (bluetoothLeAdvertiser == null) {
            stopSelf()
            return
        }
        
        // Create advertising settings - MAXIMUM POWER for better detection
        val settings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)  // Advertise frequently
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)      // Maximum transmission power
            .setConnectable(false)
            .setTimeout(0) // Advertise indefinitely
            .build()

        // Create advertising data with user ID
        // Format: RAIL_USER::<user_id>
        val payload = "RAIL_USER::$userId"
        val payloadBytes = payload.toByteArray(StandardCharsets.UTF_8)
        
        // IMPORTANT: Use manufacturer_data instead of service_data for better compatibility
        // Company ID 0xFFFF is reserved for internal use
        val data = AdvertiseData.Builder()
            .setIncludeDeviceName(false)
            .setIncludeTxPowerLevel(true)  // Include TX power to help with RSSI calculation
            .addServiceUuid(ParcelUuid(SERVICE_UUID))
            .addManufacturerData(0xFFFF, payloadBytes)  // Using manufacturer data (more reliable)
            .build()

        // Start advertising
        try {
            bluetoothLeAdvertiser?.startAdvertising(settings, data, advertiseCallback)
            android.util.Log.d("BLE_SERVICE", "Started advertising with payload: $payload")
        } catch (e: SecurityException) {
            android.util.Log.e("BLE_SERVICE", "Security exception: ${e.message}")
            e.printStackTrace()
            stopSelf()
        } catch (e: Exception) {
            android.util.Log.e("BLE_SERVICE", "Exception: ${e.message}")
            e.printStackTrace()
            stopSelf()
        }
    }

    private val advertiseCallback = object : AdvertiseCallback() {
        override fun onStartSuccess(settingsInEffect: AdvertiseSettings?) {
            super.onStartSuccess(settingsInEffect)
            android.util.Log.d("BLE_SERVICE", "✅ BLE Advertising started successfully!")
        }

        override fun onStartFailure(errorCode: Int) {
            super.onStartFailure(errorCode)
            val errorMsg = when (errorCode) {
                ADVERTISE_FAILED_DATA_TOO_LARGE -> "Data too large"
                ADVERTISE_FAILED_TOO_MANY_ADVERTISERS -> "Too many advertisers"
                ADVERTISE_FAILED_ALREADY_STARTED -> "Already started"
                ADVERTISE_FAILED_INTERNAL_ERROR -> "Internal error"
                ADVERTISE_FAILED_FEATURE_UNSUPPORTED -> "Feature unsupported"
                else -> "Unknown error: $errorCode"
            }
            android.util.Log.e("BLE_SERVICE", "❌ BLE Advertising failed: $errorMsg")
            stopSelf()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            bluetoothLeAdvertiser?.stopAdvertising(advertiseCallback)
        } catch (e: SecurityException) {
            e.printStackTrace()
        }
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }
}
