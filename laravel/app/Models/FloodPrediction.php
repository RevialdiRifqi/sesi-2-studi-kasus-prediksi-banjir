<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class FloodPrediction extends Model
{
    protected $fillable = ['input', 'probabilitas', 'level'];

    protected $casts = [
        'input' => 'array',
        'probabilitas' => 'float',
    ];
}
